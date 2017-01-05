import azure
from azure.mgmt.network.models import NetworkInterface, NetworkInterfaceIPConfiguration, IPAllocationMethod, \
    VirtualNetwork
from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error


class NetworkService(object):
    NETWORK_TYPE_TAG_NAME = 'network_type'
    SANDBOX_NETWORK_TAG_VALUE = 'sandbox'
    MGMT_NETWORK_TAG_VALUE = 'mgmt'

    def __init__(self, ip_service, tags_service):
        self.ip_service = ip_service
        self.tags_service = tags_service

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
                              logger):
        """
        This method creates a an ip address and a nic for the vm
        :param cloud_provider_model:
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
        management_group_name = cloud_provider_model.management_group_name
        sandbox_virtual_network = self.get_sandbox_virtual_network(network_client=network_client,
                                                                   group_name=management_group_name)

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
                               management_group_name,
                               network_client,
                               public_ip_address,
                               region,
                               subnet,
                               IPAllocationMethod.static,
                               tags,
                               sandbox_virtual_network.name,
                               logger)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_nic(self, interface_name, group_name, management_group_name, network_client, public_ip_address, region,
                   subnet,
                   private_ip_allocation_method, tags, virtual_network_name,
                   logger):
        """
        The method creates or updates network interface.
        Parameter
        :param logger:
        :param virtual_network_name:
        :param group_name:
        :param interface_name:
        :param management_group_name:
        :param network_client:
        :param public_ip_address:
        :param region:
        :param subnet:
        :param private_ip_allocation_method:
        :param tags:
        :return:
        """

        # private_ip_address in required only in the case of static allocation method
        # in the case of dynamic allocation method is ignored
        private_ip_address = ""
        if private_ip_allocation_method.static:
            private_ip_address = self.ip_service.get_available_private_ip(network_client, management_group_name,
                                                                          virtual_network_name,
                                                                          subnet.address_prefix[:-3],
                                                                          logger)

        operation_poller = network_client.network_interfaces.create_or_update(
                group_name,
                interface_name,
                NetworkInterface(
                        location=region,
                        ip_configurations=[
                            NetworkInterfaceIPConfiguration(
                                    name='default',
                                    private_ip_allocation_method=private_ip_allocation_method,
                                    subnet=subnet,
                                    private_ip_address=private_ip_address,
                                    public_ip_address=public_ip_address,
                            ),
                        ],
                        tags=tags
                ),
        )

        return operation_poller.result()

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
    def delete_nic(self, network_client, group_name, interface_name):
        """

        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name:
        :param interface_name:
        :return:
        """
        result = network_client.network_interfaces.delete(group_name, interface_name)

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
