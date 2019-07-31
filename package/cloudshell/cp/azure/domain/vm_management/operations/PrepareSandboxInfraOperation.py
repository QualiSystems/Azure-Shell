import traceback
from functools import partial
from multiprocessing.pool import ThreadPool
from threading import Lock

import jsonpickle
from azure.mgmt.network.models import SecurityRuleProtocol, SecurityRule, SecurityRuleAccess, RouteNextHopType
from cloudshell.cp.core.models import CreateKeysActionResult, PrepareSubnetParams, PrepareSubnetActionResult, \
    PrepareCloudInfra, PrepareCloudInfraParams, PrepareSubnet, PrepareCloudInfraResult, CreateKeys
from msrestazure.azure_exceptions import CloudError
from azure.mgmt.network.models import VirtualNetwork

from cloudshell.cp.azure.common.exceptions.virtual_network_not_found_exception import VirtualNetworkNotFoundException
from cloudshell.cp.azure.domain.services.network_service import NetworkService

from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.common.parsers.azure_resource_id_parser import AzureResourceIdParser
from cloudshell.cp.azure.models.network_actions_models import PrepareNetworkActionResult, ConnectivityActionResult, \
    PrepareNetworkParams
from cloudshell.cp.azure.models.rule_data import RuleData

INVALID_REQUEST_ERROR = 'Invalid request: {0}'


class PrepareSandboxInfraOperation(object):
    def __init__(self,
                 vm_service,
                 network_service,
                 storage_service,
                 tags_service,
                 key_pair_service,
                 security_group_service,
                 name_provider_service,
                 cancellation_service,
                 subnet_locker,
                 resource_id_parser):
        """

        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.key_pair.KeyPairService key_pair_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :param cloudshell.cp.azure.domain.services.name_provider.NameProviderService name_provider_service:
        :param cloudshell.cp.azure.domain.services.command_cancellation.CommandCancellationService cancellation_service:
        :param threading.Lock subnet_locker:
        :param AzureResourceIdParser resource_id_parser:
        :return:
        """

        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.tags_service = tags_service
        self.key_pair_service = key_pair_service
        self.security_group_service = security_group_service
        self.name_provider_service = name_provider_service
        self.cancellation_service = cancellation_service
        self.subnet_locker = subnet_locker
        self.resource_id_parser = resource_id_parser

    def action_with_cidr(action):
        return isinstance(action, PrepareCloudInfra) or isinstance(action, PrepareSubnet)

    def prepare_connectivity(self,
                             reservation,
                             cloud_provider_model,
                             storage_client,
                             resource_client,
                             network_client,
                             logger,
                             actions,
                             cancellation_context):
        """
        :param logging.Logger logger:
        :param actions:
        :param network_client:
        :param storage_client:
        :param resource_client:
        :param cloudshell.cp.azure.models.reservation_model.ReservationModel reservation:
        :param AzureCloudProviderResourceModel cloud_provider_model: cloud provider
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :return:
        """
        logger.info("PrepareConnectivity actions: {0}".format(','.join([jsonpickle.encode(a) for a in actions])))
        results = []

        # Execute prepareNetwork action first
        network_action = next((a for a in actions if action_with_cidr(a)), None)

        if not network_action:
            raise ValueError("Actions list must contain a PrepareNetworkAction.")

        cidr = network_action.actionParams.cidr

        reservation_id = reservation.reservation_id
        group_name = str(reservation_id)
        tags = self.tags_service.get_tags(reservation=reservation)
        create_key_action_result = CreateKeysActionResult()
        subnet_actions = [a for a in actions if isinstance(a, PrepareSubnet)]

        # 1. Create a resource group
        logger.info("Creating a resource group: {0} .".format(group_name))
        self.vm_service.create_resource_group(resource_management_client=resource_client, group_name=group_name,
                                              region=cloud_provider_model.region, tags=tags)

        self.cancellation_service.check_if_cancelled(cancellation_context)
        storage_account_name = self._prepare_storage_account_name(reservation_id)

        # 2+3. create storage account and keypairs (async)
        pool = ThreadPool()
        storage_res = pool.apply_async(self._create_storage_and_keypairs,
                                       (logger, storage_client, storage_account_name, group_name, cloud_provider_model,
                                        tags, cancellation_context, create_key_action_result))

        logger.info("Retrieving MGMT vNet from resource group {} by tag {}={}".format(
            cloud_provider_model.management_group_name,
            NetworkService.NETWORK_TYPE_TAG_NAME,
            NetworkService.MGMT_NETWORK_TAG_VALUE))

        virtual_networks = self.network_service \
            .get_virtual_networks(network_client=network_client,
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

        # 4. Create the sandbox NSG object
        #
        # The sandbox subnets NSG is a single NSG in sandbox that can block traffic
        # to subnets that set their attribute Public = false, i.e. private subnets
        # the idea is that all subnets in sandbox are subscribed to this subnet.

        security_group_name = self.security_group_service.get_subnets_nsg_name(reservation_id)
        logger.info("Creating a network security group: '{}' .".format(security_group_name))
        sandbox_network_security_group = self.security_group_service.create_network_security_group(
            network_client=network_client,
            group_name=group_name,
            security_group_name=security_group_name,
            region=cloud_provider_model.region,
            tags=tags)

        self.cancellation_service.check_if_cancelled(cancellation_context)

        logger.info("Creating management rules for {0}...".format(security_group_name))
        # 5. Set rules on the subnets nsg - which handles security for all subnets in sandbox.
        # Support "additional management traffic" inbound traffic
        # allow management vnet traffic
        # deny inbound from other subnets in vnet
        self._create_subnet_nsg_rules(
            group_name=group_name,
            management_vnet=management_vnet,
            network_client=network_client,
            sandbox_vnet=sandbox_vnet,
            sandbox_cidr=cidr,
            security_group_name=security_group_name,
            additional_mgmt_networks=cloud_provider_model.additional_mgmt_networks,
            logger=logger,
            subnet_actions=subnet_actions)

        self.cancellation_service.check_if_cancelled(cancellation_context)

        # 6. Create additional subnets requested by server
        for subnet in subnet_actions:
            logger.warn('creating: ' + subnet.actionParams.cidr)
            subnet_name = self.name_provider_service.format_subnet_name(group_name, subnet.actionParams.cidr)
            self._create_subnet(cidr=subnet.actionParams.cidr,
                                cloud_provider_model=cloud_provider_model,
                                logger=logger,
                                network_client=network_client,
                                resource_client=resource_client,
                                network_security_group=sandbox_network_security_group,
                                sandbox_vnet=sandbox_vnet,
                                subnet_name=subnet_name)
            results.append(self._create_result(subnet, subnet_name))

        self.cancellation_service.check_if_cancelled(cancellation_context)

        # wait for all async operations
        pool.close()
        pool.join()
        storage_res.get(timeout=900)  # will wait for 15 min and raise exception if storage account creation failed

        results.append(PrepareCloudInfraResult(self._get_action_id_by_type(actions, PrepareCloudInfra)))
        create_key_action_result.actionId = self._get_action_id_by_type(actions, CreateKeys)
        results.append(create_key_action_result)

        return results

    def _prepare_results(self, create_key_action_result, actions):
        network_action_result = PrepareCloudInfraResult(self._get_action_id_by_type(actions, PrepareCloudInfra))

        subnet_action_results = [PrepareSubnetActionResult(action_id) for action_id in
                                 self._get_action_ids_by_type(actions, PrepareSubnet)]

        create_key_action_result.actionId = self._get_action_id_by_type(actions, CreateKeys)

        return [network_action_result, create_key_action_result] + subnet_action_results

    def _get_action_id_by_type(self, actions, action_class):
        return next((action.actionId for action in actions if isinstance(action, action_class)))

    def _get_action_ids_by_type(self, actions, action_class):
        return [action.actionId for action in actions if isinstance(action, action_class)]

    def _create_result(self, item, subnet_name):
        return PrepareSubnetActionResult(item.actionId, True, 'PrepareSubnet finished successfully', '', subnet_name)

    def _prepare_storage_account_name(self, reservation_id):
        """ Storage account name in azure must be between 3-24 chars. Dashes are not allowed as well.
        :param str reservation_id:
        :rtype: str
        """
        reservation_id = reservation_id.replace("-", "")
        # we need to set a static postfix because we want to ensure we get the same storage account name if
        # prepare connectivity will run more than once
        return self.name_provider_service.generate_name(name=reservation_id, postfix="cs", max_length=24).replace("-",
                                                                                                                  "")

    def _create_storage_and_keypairs(self, logger, storage_client, storage_account_name, group_name,
                                     cloud_provider_model, tags, cancellation_context, create_key_action_result):
        """

        :param logger:
        :param storage_client:
        :param storage_account_name:
        :param group_name:
        :param cloud_provider_model:
        :param tags:
        :param cancellation_context:
        :param CreateKeysActionResult create_key_action_result:
        :return:
        """
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

            create_key_action_result.accessKey = key_pair.private_key

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

    def _create_subnet(self, cidr, cloud_provider_model, logger, network_client, resource_client,
                       network_security_group, sandbox_vnet,
                       subnet_name):
        """
        This method is atomic because we have to sync subnet creation for the entire sandbox vnet
        :param VirtualNetwork sandbox_vnet:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        """

        with self.subnet_locker:
            logger.info(
                "Creating a subnet {0} under: {1}/{2}.".format(subnet_name,
                                                               cloud_provider_model.management_group_name,
                                                               sandbox_vnet.name))
            create_subnet_command = partial(self.network_service.create_subnet,
                                            network_client=network_client,
                                            resource_group_name=cloud_provider_model.management_group_name,
                                            subnet_name=subnet_name,
                                            subnet_cidr=cidr,
                                            virtual_network=sandbox_vnet,
                                            region=cloud_provider_model.region,
                                            network_security_group=network_security_group,
                                            wait_for_result=True)
            try:
                create_subnet_command()
            except CloudError as e:
                logger.warn(e.message)
                if "NetcfgInvalidSubnet" not in str(e.error):
                    raise
                # try to cleanup stale subnet
                logger.info(
                    "Subnet with cidr {0} exist in vnet with a different name. Will try to cleanup the stale data."
                        .format(cidr))
                self._cleanup_stale_data(network_client=network_client,
                                         resource_client=resource_client,
                                         cloud_provider_model=cloud_provider_model,
                                         sandbox_vnet=sandbox_vnet,
                                         subnet_cidr=cidr,
                                         logger=logger)
                # try to create subnet again
                create_subnet_command()

    def _cleanup_stale_data(self, network_client, resource_client, cloud_provider_model, sandbox_vnet, subnet_cidr,
                            logger):
        """
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param VirtualNetwork sandbox_vnet:
        :param str subnet_cidr:
        :param logging.Logger logger:
        :return:
        """
        stale_subnets = filter(lambda x: x.address_prefix == subnet_cidr, sandbox_vnet.subnets)
        if len(stale_subnets) == 0:
            logger.info("Stale subnet with cidr {0} not found".format(subnet_cidr))
            return
        subnet = stale_subnets[0]

        if subnet.network_security_group is not None:
            logger.info("Detaching NSG from subnet {}".format(subnet.id))

            subnet.network_security_group = None
            self.network_service.update_subnet(network_client=network_client,
                                               resource_group_name=cloud_provider_model.management_group_name,
                                               virtual_network_name=sandbox_vnet.name,
                                               subnet_name=subnet.name,
                                               subnet=subnet)
            logger.info("NSG from subnet {} was successfully detached".format(subnet.id))

        resource_groups = []
        if subnet.ip_configurations is not None:
            for ip_conf in subnet.ip_configurations:
                resource_group = self.resource_id_parser.get_resource_group_name(resource_id=ip_conf.id)
                resource_groups.append(resource_group)

        logger.info("Deleting Subnet {}...".format(subnet.id))
        self.network_service.delete_subnet(network_client=network_client,
                                           group_name=cloud_provider_model.management_group_name,
                                           vnet_name=sandbox_vnet.name,
                                           subnet_name=subnet.name)

        logger.info("Subnet {} was successfully deleted".format(subnet.id))

    def _create_subnet_nsg_rules(self, group_name, management_vnet, sandbox_vnet, sandbox_cidr, network_client,
                                 security_group_name, additional_mgmt_networks, logger, subnet_actions):
        """Creates NSG management rules

        NOTE: NSG rules must be created only one by one, without concurrency
        :param str group_name: resource group name (reservation id)
        :param VirtualNetwork management_vnet: management network
        :param azure.mgmt.network.NetworkManagementClient network_client:
        :param str security_group_name: NSG name from the Azure
        :param list additional_mgmt_networks: list of additional management networks
        :param logging.Logger logger:
        """
        management_vnet_cidr = management_vnet.address_space.address_prefixes[0]
        sandbox_vnet_cidr = sandbox_vnet.address_space.address_prefixes[0]

        # RULES OVERVIEW
        #
        # Priority 2xxx:
        #   -   Allow inbound traffic from sandbox CIDR
        #   -   Deny inbound traffic from internet for subnets that requested Public = False

        # Priority 4xxx:
        #   -   Allow inbound traffic for additional management networks
        #
        # Priority 4080:
        #   -   Allow MGMT vnet cidr inbound traffic. Basically providing access to the infrastructure to manage
        #       elements in the sandbox
        #
        # Priority 4090:
        #   -   Deny inbound traffic from Sandbox VNET (the azure account vnet with
        #                                               which subnets from all sandboxes are associated.
        #       The idea is to block traffic from other sandboxes the customer has
        #

        #
        # RULES IMPLEMENTATION
        #

        #
        # PRIORITY 2xxx:
        #

        # enable access from sandbox traffic for all subnets. Note that specific VMs can block sandbox traffic using
        # the VM network security group, which is created per VM.

        for s in subnet_actions:
            subnet_cidr = s.actionParams.cidr
            security_rule_name = 'Allow_Sandbox_Traffic_To_{0}'.format(subnet_cidr.replace('/', '-'))
            allow_all_traffic = [self.allow_all_rule(security_rule_name)]

            self.security_group_service.create_network_security_group_rules(
                network_client=network_client,
                group_name=group_name,
                security_group_name=security_group_name,
                inbound_rules=allow_all_traffic,
                destination_addr=subnet_cidr,
                source_address=sandbox_cidr,
                lock=self.subnet_locker,
                start_from=2000)

            logger.info("Created security rule {0} on NSG {1}".format(security_rule_name, security_group_name))

        # block access from internet to private subnets
        private_subnets = [s for s in subnet_actions if s.actionParams and
                           s.actionParams.subnetServiceAttributes and
                           'Public' in s.actionParams.subnetServiceAttributes and
                           s.actionParams.subnetServiceAttributes['Public'] == 'False']

        for p in private_subnets:
            private_subnet_cidr = p.actionParams.cidr
            security_rule_name = 'Deny_Internet_Traffic_To_Private_Subnet_{0}' \
                .format(private_subnet_cidr.replace('/', '-'))
            deny_all_traffic = [self.deny_all_rule(security_rule_name)]

            self.security_group_service.create_network_security_group_rules(
                network_client=network_client,
                group_name=group_name,
                security_group_name=security_group_name,
                inbound_rules=deny_all_traffic,
                destination_addr=private_subnet_cidr,
                source_address=RouteNextHopType.internet,
                lock=self.subnet_locker,
                start_from=2000)

            logger.info("Created security rule {0} on NSG {1}".format(security_rule_name, security_group_name))
        #
        # PRIORITY 4xxx:
        #

        #  Allow inbound traffic from additional management networks (can configure on Azure cloud provider resource
        #  that additional networks are allowed to communicate with subnets and vms)

        for a in additional_mgmt_networks:
            security_rule_name = 'Allow_{0}_To_{1}'.format(a.replace('/', '-'), sandbox_cidr.replace('/', '-'))
            allow_traffic_from_additional_mgmt_network = [self.allow_all_rule(security_rule_name)]

            self.security_group_service.create_network_security_group_rules(
                network_client=network_client,
                group_name=group_name,
                security_group_name=security_group_name,
                inbound_rules=allow_traffic_from_additional_mgmt_network,
                destination_addr=sandbox_cidr,
                source_address=a,
                lock=self.subnet_locker,
                start_from=4000)

            logger.info("Created security rule {0} on NSG {1}".format(security_rule_name, security_group_name))
        #
        # PRIORITY 4080
        #

        #   Allow MGMT vnet cidr inbound traffic. Basically providing access to the infrastructure to manage
        #   elements in the sandbox

        security_rule_name = 'Allow_{0}_To_{1}'.format(management_vnet_cidr.replace('/', '-'),
                                                       sandbox_cidr.replace('/', '-'))
        allow_traffic_from_management_vnet_cidr = [self.allow_all_rule(security_rule_name)]

        self.security_group_service.create_network_security_group_rules(
            network_client=network_client,
            group_name=group_name,
            security_group_name=security_group_name,
            inbound_rules=allow_traffic_from_management_vnet_cidr,
            destination_addr=sandbox_cidr,
            source_address=management_vnet_cidr,
            lock=self.subnet_locker,
            start_from=4080)

        logger.info("Created security rule {0} on NSG {1}".format(security_rule_name, security_group_name))

        #
        # PRIORITY 4090
        #

        #   Deny inbound traffic from Sandbox VNET (the azure account vnet with
        #   which subnets from all sandboxes are associated.)
        #   The idea is to block traffic from other sandboxes in the account.

        security_rule_name = 'Deny_Traffic_From_Other_Sandboxes_To_Sandbox_CIDR'
        deny_all_traffic = [self.deny_all_rule(security_rule_name)]

        self.security_group_service.create_network_security_group_rules(
            network_client=network_client,
            group_name=group_name,
            security_group_name=security_group_name,
            inbound_rules=deny_all_traffic,
            destination_addr=sandbox_cidr,
            source_address=sandbox_vnet_cidr,
            lock=self.subnet_locker,
            start_from=4090)

        logger.info("Created security rule {0} on NSG {1}".format(security_rule_name, security_group_name))

    def allow_all_rule(self, security_rule_name):
        return RuleData(protocol=SecurityRuleProtocol.asterisk,
                        port='*',
                        access=SecurityRuleAccess.allow,
                        name=security_rule_name)

    def deny_all_rule(self, security_rule_name):
        return RuleData(protocol=SecurityRuleProtocol.asterisk,
                        port='*',
                        access=SecurityRuleAccess.deny,
                        name=security_rule_name)

    @staticmethod
    def _validate_management_vnet(management_vnet):
        if management_vnet is None:
            raise VirtualNetworkNotFoundException("Could not find Management Virtual Network in Azure.")

    @staticmethod
    def _validate_sandbox_vnet(sandbox_vnet):
        if sandbox_vnet is None:
            raise VirtualNetworkNotFoundException("Could not find Sandbox Virtual Network in Azure.")

    @staticmethod
    def _validate_request_and_extract_cidr(actions):
        requested_cidrs = {action.actionParams.cidr for action in actions if action_with_cidr(action)}

        if len(requested_cidrs) == 0:
            raise ValueError(INVALID_REQUEST_ERROR.format('CIDR is missing'))

        if len(requested_cidrs) > 1:
            raise ValueError("Multi subnet mode is not supported in AzureShell")

        return requested_cidrs.pop()

    @staticmethod
    def _create_fault_action_result(action, e):
        action_result = ConnectivityActionResult()
        action_result.actionId = action.actionid
        action_result.success = False
        action_result.errorMessage = 'PrepareConnectivity ended with the error: {0}'.format(e)
        return action_result


def action_with_cidr(action):
    return isinstance(action, PrepareCloudInfra) or isinstance(action, PrepareSubnet)
