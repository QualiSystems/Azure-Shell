from platform import machine

from azure.mgmt.network.models import SecurityRuleProtocol, SecurityRule, SecurityRuleAccess

from cloudshell.cp import azure

from cloudshell.cp.azure.common.operations_helper import OperationsHelper
from cloudshell.cp.azure.domain.services.tags import TagNames
from cloudshell.cp.azure.models.prepare_connectivity_action_result import PrepareConnectivityActionResult
from cloudshell.cp.azure.models.rule_data import RuleData

INVALID_REQUEST_ERROR = 'Invalid request: {0}'


class PrepareConnectivityOperation(object):
    def __init__(self,
                 logger,
                 vm_service,
                 network_service,
                 storage_service,
                 tags_service,
                 key_pair_service,
                 security_group_service):
        """

        :param logger:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.key_pair.KeyPairService key_pair_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :return:
        """

        self.logger = logger
        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.tags_service = tags_service
        self.key_pair_service = key_pair_service
        self.security_group_service = security_group_service

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
        logger.info("Creating a Key pair for the sandbox.")
        key_pair = self.key_pair_service.generate_key_pair()

        self.key_pair_service.save_key_pair(storage_client=storage_client,
                                            group_name=group_name,
                                            storage_name=storage_account_name,
                                            key_pair=key_pair)

        virtual_networks = self.network_service.get_virtual_networks(network_client=network_client,
                                                                     group_name=cloud_provider_model.management_group_name)

        management_vnet = self.network_service.get_virtual_network_by_tag(virtual_networks=virtual_networks,
                                                                          tag_key='network_type', tag_value='mgmt',
                                                                          tags_service=self.tags_service)

        if management_vnet is None:
            raise Exception("Could not find Management Virtual Network in Azure.")

        sandbox_vnet = self.network_service.get_virtual_network_by_tag(virtual_networks=virtual_networks,
                                                                       tag_key='network_type',
                                                                       tag_value='sandbox',
                                                                       tags_service=self.tags_service)

        if sandbox_vnet is None:
            raise Exception("Could not find Sandbox Virtual Network in Azure.")

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
            name = cloud_provider_model.management_group_name

            logger.info("Creating a subnet {0} under: {1)/{2}.".format(name,name,sandbox_vnet.name))

            self.network_service.create_subnet(network_client=network_client,
                                               resource_group_name=name,
                                               subnet_name=subnet_name,
                                               subnet_cidr=cidr,
                                               virtual_network=sandbox_vnet,
                                               region=cloud_provider_model.region,
                                               network_security_group=network_security_group,
                                               wait_for_result=True)

            action_result.subnet_name = subnet_name
            self.create_management_rules(group_name, management_vnet, network_client, security_group_name)

        result.append(action_result)
        return result

    def create_management_rules(self, group_name, management_vnet, network_client, security_group_name):

        # Rule 1: Deny inbound other subnets
        priority = 4000
        all = SecurityRuleProtocol.asterisk
        self.security_group_service.create_network_security_group_custom_rule(network_client=network_client,
                                                                              group_name=group_name,
                                                                              security_group_name=security_group_name,
                                                                              rule=SecurityRule(
                                                                                  access=SecurityRuleAccess.deny,
                                                                                  direction="Inbound",
                                                                                  source_address_prefix='VirtualNetwork',
                                                                                  source_port_range=all,
                                                                                  name="rule_{}".format(priority),
                                                                                  destination_address_prefix=all,
                                                                                  destination_port_range=all,
                                                                                  priority=priority,
                                                                                  protocol=all))
        # Rule 2: Allow management subnet traffic rule
        source_address_prefix = management_vnet.address_space.address_prefixes[0]
        priority = 3900
        self.security_group_service.create_network_security_group_custom_rule(network_client=network_client,
                                                                              group_name=group_name,
                                                                              security_group_name=security_group_name,
                                                                              rule=SecurityRule(
                                                                                  access=SecurityRuleAccess.allow,
                                                                                  direction="Inbound",
                                                                                  source_address_prefix=source_address_prefix,
                                                                                  source_port_range=all,
                                                                                  name="rule_{}".format(priority),
                                                                                  destination_address_prefix=all,
                                                                                  destination_port_range=all,
                                                                                  priority=priority,
                                                                                  protocol=all))

    @staticmethod
    def _extract_cidr(action):
        cidrs = next((custom_attribute.attributeValue
                      for custom_attribute in action.customActionAttributes
                      if custom_attribute.attributeName == 'Network'), None)

        if not cidrs or len(cidrs) == 0:
            raise ValueError(INVALID_REQUEST_ERROR.format('CIDR is missing'))
        return cidrs
