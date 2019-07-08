import time

import azure
from azure.mgmt.network.models import NetworkInterface, NetworkInterfaceIPConfiguration, VirtualNetwork, RouteTable, \
    Route
from retrying import retry

from cloudshell.cp.azure.common.helpers.ip_allocation_helper import is_static_allocation, to_azure_type
from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error, retryable_error_max_attempts, \
    retryable_wait_time, retry_if_retryable_error
from cloudshell.cp.azure.domain.services.security_group import SANDBOX_NSG_NAME


class NetworkService(object):
    NETWORK_TYPE_TAG_NAME = 'network_type'
    SANDBOX_NETWORK_TAG_VALUE = 'sandbox'
    MGMT_NETWORK_TAG_VALUE = 'mgmt'

    def __init__(self, ip_service, tags_service):
        self.ip_service = ip_service
        self.tags_service = tags_service

    def create_route_table(self, network_client, cloud_provider_model, routetable_request,
                           sandbox_resource_group
                           ):
        """
        :param NetworkManagementClient network_client: network client
        :param RouteTableRequestResourceModel routetable_request: route_request
        :param AzureCloudProviderResourceModel cloud_provider_model: cloud provider
        :return:
        """

        routes = []
        for route_request in routetable_request.routes:
            routes.append(Route(name=route_request.name, next_hop_ip_address=route_request.next_hope_address,
                                next_hop_type=route_request.next_hop_type,
                                address_prefix=route_request.route_address_prefix))

        route_table = RouteTable(location=cloud_provider_model.region, routes=routes)
        poller = network_client.route_tables.create_or_update(sandbox_resource_group,
                                                              routetable_request.name,
                                                              parameters=route_table)
        poller.result()

    def add_route_table_to_subnets(self, routes_rg,
                                   route_table_name, network_client,
                                   subnets, subnets_rg, subnets_vnet):
        """
        :param NetworkManagementClient network_client: network client
        :param route_table_name:
        :param subnets:
        :return:
        """
        route_table = network_client.route_tables.get(routes_rg,
                                                      route_table_name)
        for subnet in subnets:
            subnet_obj = network_client.subnets.get(subnets_rg, subnets_vnet, subnet)
            subnet_obj.route_table = route_table
            poller = network_client.subnets.create_or_update(subnets_rg, subnets_vnet, subnet, subnet_obj)
            poller.result()

    def create_network_for_vm(self,
                              network_client,
                              group_name,
                              interface_name,
                              ip_name,
                              cloud_provider_model,
                              subnet,
                              tags,
                              add_public_ip,
                              public_ip_type,
                              logger,
                              reservation_id,
                              cloudshell_session,
                              network_security_group=None):
        """
        This method creates a an ip address and a nic for the vm
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session:
        :param str reservation_id:
        :param azure.mgmt.network.models.NetworkSecurityGroup network_security_group:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param public_ip_type:
        :param add_public_ip:
        :param network_client:
        :param group_name:
        :param interface_name:
        :param ip_name:
        :param region:
        :param subnet:
        :param tags:
        :rtype: NetworkInterface
        """

        region = cloud_provider_model.region

        # 1. Create ip address
        public_ip_address = None
        if add_public_ip:
            public_ip_address = self._create_public_ip(
                network_client=network_client,
                region=region,
                group_name=group_name,
                ip_name=ip_name,
                public_ip_type=public_ip_type,
                tags=tags)

        # 2. Create NIC
        return self.create_nic(interface_name,
                               group_name,
                               network_client,
                               public_ip_address,
                               region,
                               subnet,
                               to_azure_type(cloud_provider_model.private_ip_allocation_method),
                               tags,
                               logger,
                               reservation_id,
                               cloudshell_session,
                               network_security_group)

    @retry(stop_max_attempt_number=5,
           wait_fixed=2000,
           retry_on_exception=retry_if_connection_error)
    @retry(stop_max_attempt_number=retryable_error_max_attempts,
           wait_fixed=retryable_wait_time,
           retry_on_exception=retry_if_retryable_error)
    def create_nic(self, interface_name, group_name, network_client, public_ip_address, region,
                   subnet, private_ip_allocation_method, tags, logger, reservation_id, cloudshell_session,
                   network_security_group=None):
        """
        The method creates or updates network interface.
        Parameter
        :param azure.mgmt.network.models.NetworkSecurityGroup network_security_group:
        :param logger:
        :param group_name:
        :param interface_name:
        :param network_client:
        :param public_ip_address:
        :param region:
        :param subnet:
        :param str private_ip_allocation_method:
        :param tags:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session:
        :param str reservation_id:
        :return:
        """

        # private_ip_address in required only in the case of static allocation method
        # in the case of dynamic allocation method is ignored
        # purpose of static allocation -> on restart machine, the ip can get lost. By using static we ensure the ip
        # will remain the same

        private_ip_address = None
        if is_static_allocation(private_ip_allocation_method):
            private_ip_address = self.ip_service.get_next_available_ip_from_cs_pool(logger=logger,
                                                                                    api=cloudshell_session,
                                                                                    reservation_id=reservation_id,
                                                                                    subnet_cidr=subnet.address_prefix)

        ip_config = NetworkInterfaceIPConfiguration(name='default',
                                                    private_ip_allocation_method=private_ip_allocation_method,
                                                    subnet=subnet,
                                                    private_ip_address=private_ip_address,
                                                    public_ip_address=public_ip_address)

        network_interface = NetworkInterface(location=region,
                                             network_security_group=network_security_group,
                                             ip_configurations=[ip_config],
                                             tags=tags)

        start_time = time.time()

        operation_poller = network_client.network_interfaces.create_or_update(
            group_name,
            interface_name,
            network_interface)

        # wait for nic to be created
        # todo - if nic creation failed release checked out ip from pool
        nic = operation_poller.result()
        elapsed_time = time.time() - start_time
        logger.info("Done creating nic '{}'. Operation took {} seconds".format(nic.name, elapsed_time))

        return nic

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def _create_public_ip(self, network_client, region, group_name, ip_name, public_ip_type, tags):
        """Create Azure Public IP resource

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param region: (str) Azure region
        :param group_name: (str) resource group name (reservation id)
        :param ip_name: (str) name for Azure Public IP resource
        :param public_ip_type: (str) IP Allocation method for the Public IP ("Static"/"Dynamic")
        :param tags: Azure tags
        :return: azure.mgmt.network.models.PublicIPAddress instance
        """
        public_ip_allocation_method = self._get_ip_allocation_type(public_ip_type)

        operation_poller = network_client.public_ip_addresses.create_or_update(
            group_name,
            ip_name,
            azure.mgmt.network.models.PublicIPAddress(
                location=region,
                public_ip_allocation_method=public_ip_allocation_method,
                idle_timeout_in_minutes=4,
                tags=tags
            ),
        )

        return operation_poller.result()

    def _get_ip_allocation_type(self, ip_type):
        """Get corresponding Enum type by string ip_type

        :param ip_type: (str) IP Allocation method for the Public IP ("Static"/"Dynamic")
        :return: static/dynamic property from azure.mgmt.network.models.IPAllocationMethod Enum
        :raise Exception if ip_type is invalid
        """
        types_map = {
            "static": azure.mgmt.network.models.IPAllocationMethod.static,
            "dynamic": azure.mgmt.network.models.IPAllocationMethod.dynamic,
        }

        allocation_type = types_map.get(ip_type.lower())

        if not allocation_type:
            raise Exception("Incorrect allocation type {}. Possible values are {}"
                            .format(ip_type, [type_map.title() for type_map in types_map.iterkeys()]))

        return allocation_type

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_subnet(self, network_client,
                      resource_group_name,
                      subnet_name,
                      subnet_cidr,
                      virtual_network,
                      region,
                      network_security_group=None,
                      wait_for_result=False):
        """

        :param network_security_group:
        :param wait_for_result:
        :param subnet_name:
        :param region:
        :param virtual_network:
        :param subnet_cidr:
        :param resource_group_name:
        :param azure.mgmt.network.NetworkManagementClient network_client:

        :return:
        """

        operation_poller = network_client.subnets.create_or_update(resource_group_name,
                                                                   virtual_network.name,
                                                                   subnet_name,
                                                                   azure.mgmt.network.models.Subnet(
                                                                       address_prefix=subnet_cidr,
                                                                       network_security_group=network_security_group))

        if wait_for_result:
            return operation_poller.result()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def update_subnet(self, network_client, resource_group_name, virtual_network_name, subnet_name, subnet):
        """

        :param azure.mgmt.network.NetworkManagementClient network_client:
        :param resource_group_name:
        :param virtual_network_name:
        :param subnet_name:
        :param azure.mgmt.network.models.Subnet subnet:
        """
        operation_poller = network_client.subnets.create_or_update(resource_group_name,
                                                                   virtual_network_name,
                                                                   subnet_name,
                                                                   subnet)
        return operation_poller.result()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_virtual_network(self, management_group_name,
                               network_client,
                               network_name,
                               region,
                               subnet_name,
                               tags,
                               vnet_cidr,
                               subnet_cidr,
                               network_security_group):
        """
        Creates a virtual network with a subnet
        :param management_group_name:
        :param network_client:
        :param network_name:
        :param region:
        :param subnet_name:
        :param tags:
        :param vnet_cidr:
        :param subnet_cidr:
        :param network_security_group:
        :return:
        """
        result = network_client.virtual_networks.create_or_update(
            management_group_name,
            network_name,
            azure.mgmt.network.models.VirtualNetwork(
                location=region,
                tags=tags,
                address_space=azure.mgmt.network.models.AddressSpace(
                    address_prefixes=[
                        vnet_cidr,
                    ],
                ),
                subnets=[
                    azure.mgmt.network.models.Subnet(
                        network_security_group=network_security_group,
                        name=subnet_name,
                        address_prefix=subnet_cidr,
                    ),
                ],
            ),
            tags=tags
        )
        result.wait()
        subnet = network_client.subnets.get(management_group_name, network_name, subnet_name)
        return subnet

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_public_ip(self, network_client, group_name, ip_name):
        """

        :param network_client:
        :param group_name:
        :param ip_name:
        :return:
        """

        return network_client.public_ip_addresses.get(group_name, ip_name)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_private_ip(self, network_client, group_name, vm_name):
        """

        :param network_client:
        :param group_name:
        :param vm_name:
        """
        nic = network_client.network_interfaces.get(group_name, vm_name)
        return nic.ip_configurations[0].private_ip_address

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_nics(self, network_client, group_name, interface_names):
        """

        :param interface_names:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name:
        :return:
        """
        for interface_name in interface_names:
            result = network_client.network_interfaces.delete(group_name, interface_name)
            result.wait()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_nic(self, network_client, group_name, interface_name):
        """

        :param interface_name:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name:
        :return:
        """
        result = network_client.network_interfaces.delete(group_name, interface_name)
        result.wait()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_ips(self, network_client, group_name, public_ip_names):
        """

        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name: (str) resource group name (reservation id)
        :param ip_name: (str) name for Azure Public IP resource
        :return:
        """
        for ip_name in public_ip_names:
            result = network_client.public_ip_addresses.delete(group_name, ip_name)
            result.wait()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_ip(self, network_client, group_name, ip_name):
        """

        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name: (str) resource group name (reservation id)
        :param ip_name: (str) name for Azure Public IP resource
        :return:
        """
        result = network_client.public_ip_addresses.delete(group_name, ip_name)
        result.wait()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_subnet(self, network_client, group_name, vnet_name, subnet_name):
        """

        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient instance
        :param group_name: (str) resource group name (reservation id)
        :param vnet_name: (str) virtual network name
        :param subnet_name: (str) subnet name
        :return:
        """
        result = network_client.subnets.delete(resource_group_name=group_name,
                                               virtual_network_name=vnet_name,
                                               subnet_name=subnet_name)
        result.wait()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_virtual_networks(self, network_client, group_name):
        """
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param str group_name:
        :return: list of vNets in group
        :rtype: list[VirtualNetwork]
        """
        networks_list = network_client.virtual_networks.list(group_name)
        return list(networks_list)

    def get_sandbox_virtual_network(self, network_client, group_name):
        """
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param str group_name:
        :return:
        :rtype: VirtualNetwork
        """

        virtual_networks = self.get_virtual_networks(network_client=network_client,
                                                     group_name=group_name)

        return self.get_virtual_network_by_tag(virtual_networks=virtual_networks,
                                               tag_key=NetworkService.NETWORK_TYPE_TAG_NAME,
                                               tag_value=NetworkService.SANDBOX_NETWORK_TAG_VALUE)

    def get_virtual_network_by_tag(self, virtual_networks, tag_key, tag_value):
        """
        :param list[VirtualNetwork] virtual_networks:
        :param str tag_key:
        :param str tag_value:
        :return:
        :rtype: VirtualNetwork
        """
        return next((network for network in virtual_networks
                     if network and self.tags_service.try_find_tag(
            tags_list=network.tags, tag_key=tag_key) == tag_value),
                    None)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_nsg_artifacts_associated_with_vm(self, network_client, resource_group_name, vm_name):
        """
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param str resource_group_name:
        :param str vm_name:
        """

        network_security_groups = network_client.network_security_groups.list(resource_group_name)
        for nsg in network_security_groups:
            if vm_name in nsg.name:
                # rollback vm nsg
                poller = network_client.network_security_groups.delete(resource_group_name,
                                                                       nsg.name)
                poller.wait()

            if SANDBOX_NSG_NAME in nsg.name:
                for rule in nsg.security_rules:
                    if vm_name in rule.name:
                        # rollback inbound ports
                        poller = network_client.security_rules.delete(resource_group_name,
                                                                      nsg.name,
                                                                      rule.name)
                        poller.wait()
