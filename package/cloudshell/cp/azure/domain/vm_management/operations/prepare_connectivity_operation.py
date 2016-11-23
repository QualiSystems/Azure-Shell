import traceback
from threading import Lock
from azure.mgmt.network.models import SecurityRuleProtocol, SecurityRule, SecurityRuleAccess
from msrest.exceptions import ClientRequestError
from requests.packages.urllib3.exceptions import ConnectionError
from retrying import retry

from cloudshell.cp.azure.common.exceptions.virtual_network_not_found_exception import VirtualNetworkNotFoundException
from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error
from cloudshell.cp.azure.common.operations_helper import OperationsHelper
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.models.prepare_connectivity_action_result import PrepareConnectivityActionResult

INVALID_REQUEST_ERROR = 'Invalid request: {0}'


class PrepareConnectivityOperation(object):
    def __init__(self,
                 vm_service,
                 network_service,
                 storage_service,
                 tags_service,
                 key_pair_service,
                 security_group_service):
        """

        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.key_pair.KeyPairService key_pair_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :return:
        """

        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.tags_service = tags_service
        self.key_pair_service = key_pair_service
        self.security_group_service = security_group_service
        self.subnet_locker = Lock()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def prepare_connectivity(self,
                             reservation,
                             cloud_provider_model,
                             storage_client,
                             resource_client,
                             network_client,
                             logger,
                             request):
        """
        :param logging.Logger logger:
        :param request:
        :param network_client:
        :param storage_client:
        :param resource_client:
        :param cloudshell.cp.azure.models.reservation_model.ReservationModel reservation:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :return:
        """
        async_operations = []  # list of AzureOperationPoller
        reservation_id = reservation.reservation_id
        group_name = str(reservation_id)
        subnet_name = group_name
        tags = self.tags_service.get_tags(reservation=reservation)
        result = []
        action_result = PrepareConnectivityActionResult()

        # 1. Create a resource group
        logger.info("Creating a resource group: {0} .".format(group_name))
        self.vm_service.create_resource_group(resource_management_client=resource_client, group_name=group_name,
                                              region=cloud_provider_model.region, tags=tags)

        storage_account_name = OperationsHelper.generate_name(reservation_id)

        # 2. Create a storage account
        logger.info("Creating a storage account {0} .".format(storage_account_name))
        action_result.storage_name = self.storage_service.create_storage_account(storage_client=storage_client,
                                                                                 group_name=group_name,
                                                                                 region=cloud_provider_model.region,
                                                                                 storage_account_name=storage_account_name,
                                                                                 tags=tags,
                                                                                 wait_until_created=True)
        # 3 Create a Key pair for the sandbox
        logger.info("Creating a SSH key pair in the storage account {}".format(storage_account_name))
        self._create_key_pair(group_name=group_name,
                              storage_account_name=storage_account_name,
                              storage_client=storage_client)

        logger.info("Retrieving MGMT vNet from resource group {} by tag {}={}".format(
                cloud_provider_model.management_group_name,
                NetworkService.NETWORK_TYPE_TAG_NAME,
                NetworkService.MGMT_NETWORK_TAG_VALUE))

        virtual_networks = self.network_service.get_virtual_networks(network_client=network_client,
                                                                     group_name=cloud_provider_model.management_group_name)

        management_vnet = self.network_service.get_virtual_network_by_tag(virtual_networks=virtual_networks,
                                                                          tag_key=NetworkService.NETWORK_TYPE_TAG_NAME,
                                                                          tag_value=NetworkService.MGMT_NETWORK_TAG_VALUE,
                                                                          tags_service=self.tags_service)

        self._validate_management_vnet(management_vnet)

        logger.info("Retrieving sandbox vNet from resource group {} by tag {}={}".format(
                cloud_provider_model.management_group_name,
                NetworkService.NETWORK_TYPE_TAG_NAME,
                NetworkService.SANDBOX_NETWORK_TAG_VALUE))

        sandbox_vnet = self.network_service.get_virtual_network_by_tag(virtual_networks=virtual_networks,
                                                                       tag_key=NetworkService.NETWORK_TYPE_TAG_NAME,
                                                                       tag_value=NetworkService.SANDBOX_NETWORK_TAG_VALUE,
                                                                       tags_service=self.tags_service)

        self._validate_sandbox_vnet(sandbox_vnet)

        # 4.Create the NSG object
        security_group_name = OperationsHelper.generate_name(reservation_id)
        logger.info("Creating a network security group '{}' .".format(security_group_name))
        network_security_group = self.security_group_service.create_network_security_group(
                network_client=network_client,
                group_name=group_name,
                security_group_name=security_group_name,
                region=cloud_provider_model.region,
                tags=tags)

        for action in request.actions:
            cidr = self._extract_cidr(action)
            logger.info("Received CIDR {0} from server".format(cidr))

            # 5. Create a subnet
            self._create_subnet(cidr=cidr,
                                cloud_provider_model=cloud_provider_model,
                                logger=logger,
                                network_client=network_client,
                                network_security_group=network_security_group,
                                sandbox_vnet=sandbox_vnet,
                                subnet_name=subnet_name)

            logger.info("Creating NSG management rules...")

            async_rules_operations = self._create_management_rules(
                    group_name=group_name,
                    management_vnet=management_vnet,
                    network_client=network_client,
                    security_group_name=security_group_name,
                    logger=logger)

            async_operations += async_rules_operations
            action_result.subnet_name = subnet_name

        # wait for all async operations
        logger.info("Waiting for async create operations to be done...")
        for operation_poller in async_operations:
            operation_poller.wait()

        result.append(action_result)
        return result

    def _create_key_pair(self, group_name, storage_account_name, storage_client):
        key_pair = self.key_pair_service.generate_key_pair()
        self.key_pair_service.save_key_pair(storage_client=storage_client,
                                            group_name=group_name,
                                            storage_name=storage_account_name,
                                            key_pair=key_pair)

    def _create_subnet(self, cidr, cloud_provider_model, logger, network_client, network_security_group, sandbox_vnet,
                       subnet_name):
        """
        This method is atomic
        """
        with self.subnet_locker:
            logger.info(
                    "Creating a subnet {0} under: {1}/{2}.".format(subnet_name,
                                                                   cloud_provider_model.management_group_name,
                                                                   sandbox_vnet.name))
            self.network_service.create_subnet(network_client=network_client,
                                               resource_group_name=cloud_provider_model.management_group_name,
                                               subnet_name=subnet_name,
                                               subnet_cidr=cidr,
                                               virtual_network=sandbox_vnet,
                                               region=cloud_provider_model.region,
                                               network_security_group=network_security_group,
                                               wait_for_result=True)

    def _create_management_rules(self, group_name, management_vnet, network_client, security_group_name, logger):
        """Creates NSG management rules

        :param group_name: (str) resource group name (reservation id)
        :param management_vnet: (str) management network
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param security_group_name: NSG name from the Azure
        :param logger: logging.Logger instance
        :return: [msrestazure.azure_operation.AzureOperationPoller, ...] list of AzureOperationPoller for created rules
        """
        all_symbol = SecurityRuleProtocol.asterisk
        async_operations = []
        priority = 4000
        logger.info("Creating (async) NSG rule to deny inbound traffic from other subnets with priority {}"
                    .format(priority))

        operation_poller = self.security_group_service.create_network_security_group_custom_rule(
                network_client=network_client,
                group_name=group_name,
                security_group_name=security_group_name,
                rule=SecurityRule(
                        access=SecurityRuleAccess.deny,
                        direction="Inbound",
                        source_address_prefix='VirtualNetwork',
                        source_port_range=all_symbol,
                        name="rule_{}".format(priority),
                        destination_address_prefix=all_symbol,
                        destination_port_range=all_symbol,
                        priority=priority,
                        protocol=all_symbol),
                async=True)

        async_operations.append(operation_poller)

        # Rule 2:
        source_address_prefix = management_vnet.address_space.address_prefixes[0]
        priority = 3900
        logger.info("Creating (async) NSG rule to allow management subnet traffic with priority {}".format(priority))

        operation_poller = self.security_group_service.create_network_security_group_custom_rule(
                network_client=network_client,
                group_name=group_name,
                security_group_name=security_group_name,
                rule=SecurityRule(
                        access=SecurityRuleAccess.allow,
                        direction="Inbound",
                        source_address_prefix=source_address_prefix,
                        source_port_range=all_symbol,
                        name="rule_{}".format(priority),
                        destination_address_prefix=all_symbol,
                        destination_port_range=all_symbol,
                        priority=priority,
                        protocol=all_symbol),
                async=True)

        async_operations.append(operation_poller)

        return async_operations

    @staticmethod
    def _validate_management_vnet(management_vnet):
        if management_vnet is None:
            raise VirtualNetworkNotFoundException("Could not find Management Virtual Network in Azure.")

    @staticmethod
    def _validate_sandbox_vnet(sandbox_vnet):
        if sandbox_vnet is None:
            raise VirtualNetworkNotFoundException("Could not find Sandbox Virtual Network in Azure.")

    @staticmethod
    def _extract_cidr(action):
        cidrs = next((custom_attribute.attributeValue
                      for custom_attribute in action.customActionAttributes
                      if custom_attribute.attributeName == 'Network'), None)

        if not cidrs or len(cidrs) == 0:
            raise ValueError(INVALID_REQUEST_ERROR.format('CIDR is missing'))
        return cidrs
