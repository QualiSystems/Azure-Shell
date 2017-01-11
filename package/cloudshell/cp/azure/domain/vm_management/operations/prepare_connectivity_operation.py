import traceback
from multiprocessing.pool import ThreadPool
from threading import Lock

from azure.mgmt.network.models import SecurityRuleProtocol, SecurityRule, SecurityRuleAccess

from cloudshell.cp.azure.common.exceptions.virtual_network_not_found_exception import VirtualNetworkNotFoundException
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
                 security_group_service,
                 cryptography_service,
                 name_provider_service,
                 cancellation_service,
                 subnet_locker):
        """

        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.key_pair.KeyPairService key_pair_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :param cloudshell.cp.azure.domain.services.cryptography_service.CryptographyService cryptography_service:
        :param cloudshell.cp.azure.domain.services.name_provider.NameProviderService name_provider_service:
        :param cloudshell.cp.azure.domain.services.command_cancellation.CommandCancellationService cancellation_service:
        :param threading.Lock subnet_locker:
        :return:
        """

        self.cryptography_service = cryptography_service
        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.tags_service = tags_service
        self.key_pair_service = key_pair_service
        self.security_group_service = security_group_service
        self.name_provider_service = name_provider_service
        self.cancellation_service = cancellation_service
        self.subnet_locker = subnet_locker

    def prepare_connectivity(self,
                             reservation,
                             cloud_provider_model,
                             storage_client,
                             resource_client,
                             network_client,
                             logger,
                             request,
                             cancellation_context):
        """
        :param logging.Logger logger:
        :param request:
        :param network_client:
        :param storage_client:
        :param resource_client:
        :param cloudshell.cp.azure.models.reservation_model.ReservationModel reservation:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
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

        self.cancellation_service.check_if_cancelled(cancellation_context)
        storage_account_name = self.name_provider_service.generate_name(reservation_id)

        # 2+3. create storage account and keypairs (async)
        pool = ThreadPool()
        storage_res = pool.apply_async(self._create_storage_and_keypairs,
                                       (logger, storage_client, storage_account_name, group_name, cloud_provider_model,
                                        tags, cancellation_context, action_result))

        logger.info("Retrieving MGMT vNet from resource group {} by tag {}={}".format(
            cloud_provider_model.management_group_name,
            NetworkService.NETWORK_TYPE_TAG_NAME,
            NetworkService.MGMT_NETWORK_TAG_VALUE))

        virtual_networks = self.network_service.get_virtual_networks(network_client=network_client,
                                                                     group_name=cloud_provider_model.management_group_name)

        self.cancellation_service.check_if_cancelled(cancellation_context)
        
        management_vnet = self.network_service.get_virtual_network_by_tag(        
            virtual_networks=virtual_networks,        
            tag_key=NetworkService.NETWORK_TYPE_TAG_NAME,
            tag_value=NetworkService.MGMT_NETWORK_TAG_VALUE)

        self._validate_management_vnet(management_vnet)

        logger.info("Retrieving sandbox vNet from resource group {} by tag {}={}".format(
            cloud_provider_model.management_group_name,
            NetworkService.NETWORK_TYPE_TAG_NAME,
            NetworkService.SANDBOX_NETWORK_TAG_VALUE))

        sandbox_vnet = self.network_service.get_virtual_network_by_tag(
            virtual_networks=virtual_networks,
            tag_key=NetworkService.NETWORK_TYPE_TAG_NAME,
            tag_value=NetworkService.SANDBOX_NETWORK_TAG_VALUE)

        self._validate_sandbox_vnet(sandbox_vnet)

        # 4. Create the NSG object
        security_group_name = self.name_provider_service.generate_name(reservation_id)
        logger.info("Creating a network security group '{}' .".format(security_group_name))
        network_security_group = self.security_group_service.create_network_security_group(
            network_client=network_client,
            group_name=group_name,
            security_group_name=security_group_name,
            region=cloud_provider_model.region,
            tags=tags)

        self.cancellation_service.check_if_cancelled(cancellation_context)

        cidr = self._extract_cidr(request)
        logger.info("Received CIDR {0} from server".format(cidr))

        logger.info("Creating NSG management rules...")
        # 5. Set rules on NSG to create a sandbox
        self._create_management_rules(
            group_name=group_name,
            management_vnet=management_vnet,
            network_client=network_client,
            sandbox_vnet_cidr=cidr,
            security_group_name=security_group_name,
            additional_mgmt_networks=cloud_provider_model.additional_mgmt_networks,
            logger=logger)

        self.cancellation_service.check_if_cancelled(cancellation_context)

        # 6. Create a subnet with NSG
        self._create_subnet(cidr=cidr,
                            cloud_provider_model=cloud_provider_model,
                            logger=logger,
                            network_client=network_client,
                            network_security_group=network_security_group,
                            sandbox_vnet=sandbox_vnet,
                            subnet_name=subnet_name)

        self.cancellation_service.check_if_cancelled(cancellation_context)

        # wait for all async operations
        pool.close()
        pool.join()
        storage_res.get(timeout=900)  # will wait for 15 min and raise exception if storage account creation failed

        action_result.storage_name = storage_account_name
        action_result.subnet_name = subnet_name
        result.append(action_result)
        return result

    def _create_storage_and_keypairs(self, logger, storage_client, storage_account_name, group_name,
                                     cloud_provider_model, tags, cancellation_context, action_result):

        try:
            # 2. Create a storage account
            logger.info("Creating a storage account {0} .".format(storage_account_name))
            self.storage_service.create_storage_account(storage_client=storage_client,
                                                        group_name=group_name,
                                                        region=cloud_provider_model.region,
                                                        storage_account_name=storage_account_name,
                                                        tags=tags,
                                                        wait_until_created=True)

            self.cancellation_service.check_if_cancelled(cancellation_context)

            # 3 Create a Key pair for the sandbox
            logger.info("Creating an SSH key pair in the storage account {}".format(storage_account_name))
            key_pair = self._create_key_pair(group_name=group_name,
                                             storage_account_name=storage_account_name,
                                             storage_client=storage_client)

            self.cancellation_service.check_if_cancelled(cancellation_context)

            cryptography_dto = self.cryptography_service.encrypt(key_pair.private_key)

            action_result.access_key = cryptography_dto.encrypted_input
            action_result.secret_key = cryptography_dto.encrypted_asymmetric_key
        except Exception as exc:
            logger.error(traceback.format_exc())
            raise

        return True

    def _wait_on_operations(self, async_operations, logger):
        logger.info("Waiting for async create operations to be done... {}".format(async_operations))
        for operation_poller in async_operations:
            operation_poller.wait()

    def _create_key_pair(self, group_name, storage_account_name, storage_client):
        key_pair = self.key_pair_service.generate_key_pair()
        self.key_pair_service.save_key_pair(storage_client=storage_client,
                                            group_name=group_name,
                                            storage_name=storage_account_name,
                                            key_pair=key_pair)
        return key_pair

    def _create_subnet(self, cidr, cloud_provider_model, logger, network_client, network_security_group, sandbox_vnet,
                       subnet_name):
        """
        This method is atomic because we have to sync subnet creation for the entire sandbox vnet
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

    def _create_management_rules(self, group_name, management_vnet, sandbox_vnet_cidr, network_client,
                                 security_group_name, additional_mgmt_networks, logger):
        """Creates NSG management rules

        NOTE: NSG rules must be created only one by one, without concurrency
        :param str group_name: resource group name (reservation id)
        :param str management_vnet: management network
        :param azure.mgmt.network.NetworkManagementClient network_client:
        :param str security_group_name: NSG name from the Azure
        :param list additional_mgmt_networks: list of additional management networks
        :param logging.Logger logger:
        """
        used_priorities = []
        all_symbol = SecurityRuleProtocol.asterisk

        # rule 0
        priority = 3950
        used_priorities.append(priority)
        logger.info("Creating NSG rule to deny inbound traffic from other subnets with priority {}..."
                    .format(priority))

        operation_poller = self.security_group_service.create_network_security_group_custom_rule(
            network_client=network_client,
            group_name=group_name,
            security_group_name=security_group_name,
            rule=SecurityRule(
                access=SecurityRuleAccess.allow,
                direction="Inbound",
                source_address_prefix=sandbox_vnet_cidr,
                source_port_range=all_symbol,
                name="rule_{}".format(priority),
                destination_address_prefix=sandbox_vnet_cidr,
                destination_port_range=all_symbol,
                priority=priority,
                protocol=all_symbol),
            async=True)

        # can't create next rule while previous is in the deploying state
        operation_poller.wait()

        # Rule 1
        priority = 4000
        used_priorities.append(priority)
        logger.info("Creating NSG rule to deny inbound traffic from other subnets with priority {}..."
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

        # can't create next rule while previous is in the deploying state
        operation_poller.wait()

        # Rule 2:
        source_address_prefix = management_vnet.address_space.address_prefixes[0]
        priority = 3900
        used_priorities.append(priority)
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
        operation_poller.wait()

        # free priorities for additional NSG rules
        mgmt_rules_priorities = (priority for priority in xrange(3900, 4001, 5) if priority not in used_priorities)

        # create NSG rules for additional management networks
        logger.info("Creating NSG rules to allow traffic from additional management networks...")
        for additional_network, priority in zip(additional_mgmt_networks, mgmt_rules_priorities):
            logger.info("Creating NSG rule for additional management network {} with priority {} ..."
                        .format(additional_network, priority))
            self.security_group_service.create_network_security_group_custom_rule(
                network_client=network_client,
                group_name=group_name,
                security_group_name=security_group_name,
                rule=SecurityRule(
                    access=SecurityRuleAccess.allow,
                    direction="Inbound",
                    source_address_prefix=additional_network,
                    source_port_range=all_symbol,
                    name="rule_{}".format(priority),
                    destination_address_prefix=all_symbol,
                    destination_port_range=all_symbol,
                    priority=priority,
                    protocol=all_symbol),
                async=False)

    @staticmethod
    def _validate_management_vnet(management_vnet):
        if management_vnet is None:
            raise VirtualNetworkNotFoundException("Could not find Management Virtual Network in Azure.")

    @staticmethod
    def _validate_sandbox_vnet(sandbox_vnet):
        if sandbox_vnet is None:
            raise VirtualNetworkNotFoundException("Could not find Sandbox Virtual Network in Azure.")

    @staticmethod
    def _extract_cidr(request):
        # get first or default
        action = next(iter(request.actions or []), None)
        if action is None:
            raise ValueError("Action is missing in request. Request: {}".format(request))

        cidrs = next((custom_attribute.attributeValue
                      for custom_attribute in action.customActionAttributes
                      if custom_attribute.attributeName == 'Network'), None)

        if not cidrs or len(cidrs) == 0:
            raise ValueError(INVALID_REQUEST_ERROR.format('CIDR is missing'))
        return cidrs
