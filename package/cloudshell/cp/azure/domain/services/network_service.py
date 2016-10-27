import azure
from azure.mgmt.network.models import NetworkInterface, NetworkInterfaceIPConfiguration, IPAllocationMethod


class NetworkService(object):
    def __init__(self):
        pass

    def create_network_for_vm(self,
                              network_client,
                              group_name,
                              interface_name,
                              ip_name,
                              region,
                              subnet,
                              tags,
                              add_public_ip,
                              public_ip_type):
        """
        This method creates a an ip address and a nic for the vm
        :param public_ip_type:
        :param add_public_ip:
        :param network_client:
        :param group_name:
        :param interface_name:
        :param ip_name:
        :param region:
        :param subnet:
        :param tags:
        :return:
        """
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
        result = self.create_nic(interface_name,
                                 group_name,
                                 network_client,
                                 public_ip_address,
                                 region,
                                 subnet,
                                 IPAllocationMethod.dynamic,
                                 tags)

        # 3. update the type of private ip from dynamic to static (ip itself must be supplied)
        private_ip_address = result.result().ip_configurations[0].private_ip_address
        self.create_nic_with_static_private_ip(interface_name,
                                               group_name,
                                               network_client,
                                               private_ip_address,
                                               public_ip_address,
                                               region,
                                               subnet,
                                               tags)

        network_interface = network_client.network_interfaces.get(
            group_name,
            interface_name,
        )

        return network_interface.id

    def create_nic_with_static_private_ip(self, interface_name, management_group_name, network_client,
                                          private_ip_address,
                                          public_ip_address, region, subnet, tags):
        """

        :param interface_name:
        :param management_group_name:
        :param network_client:
        :param private_ip_address:
        :param public_ip_address:
        :param region:
        :param subnet:
        :param tags:
        :return:
        """
        result = network_client.network_interfaces.create_or_update(
            management_group_name,
            interface_name,
            NetworkInterface(
                location=region,
                ip_configurations=[
                    NetworkInterfaceIPConfiguration(
                        name='default',
                        private_ip_allocation_method=IPAllocationMethod.static,
                        private_ip_address=private_ip_address,
                        subnet=subnet,
                        public_ip_address=public_ip_address,
                    ),
                ],
                tags=tags
            ),
        )
        result.wait()

    def create_nic(self, interface_name, management_group_name, network_client, public_ip_address, region, subnet,
                   private_ip_allocation_method, tags):
        """

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
        result = network_client.network_interfaces.create_or_update(
            management_group_name,
            interface_name,
            NetworkInterface(
                location=region,
                ip_configurations=[
                    NetworkInterfaceIPConfiguration(
                        name='default',
                        private_ip_allocation_method=private_ip_allocation_method,
                        subnet=subnet,
                        public_ip_address=public_ip_address,
                    ),
                ],
                tags=tags
            ),
        )
        result.wait()
        return result

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

    def create_subnet(self, network_client,
                      resource_group_name,
                      subnet_name,
                      subnet_cidr,
                      virtual_network,
                      region,
                      wait_for_result=False):
        """

        :param wait_for_result:
        :param subnet_name:
        :param region:
        :param virtual_network:
        :param subnet_cidr:
        :param resource_group_name:
        :param azure.mgmt.network.NetworkManagementClient network_client:

        :return:
        """

        result = network_client.subnets.create_or_update(resource_group_name,
                                                         virtual_network.name,
                                                         subnet_name,
                                                         azure.mgmt.network.models.Subnet(address_prefix=subnet_cidr))

        if wait_for_result:
            result.wait()


    def create_virtual_network(self, management_group_name,
                               network_client,
                               network_name,
                               region,
                               subnet_name,
                               tags,
                               vnet_cidr,
                               subnet_cidr):
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

    def get_public_ip(self, network_client, group_name, ip_name):
        """

        :param network_client:
        :param group_name:
        :param ip_name:
        :return:
        """

        return network_client.public_ip_addresses.get(group_name, ip_name)

    def delete_nic(self, network_client, group_name, interface_name):
        """

        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name:
        :param interface_name:
        :return:
        """
        result = network_client.network_interfaces.delete(group_name, interface_name)

        result.wait()

    def delete_ip(self, network_client, group_name, ip_name):
        """

        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name:
        :param ip_name:
        :return:
        """
        result = network_client.public_ip_addresses.delete(group_name, ip_name)

    def get_virtual_networks(self, network_client, group_name):
        """

        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name:
        :return:
        """
        networks_list = network_client.virtual_networks.list(group_name)
        return list(networks_list)
