import azure
from azure.mgmt.network.models import NetworkInterface, NetworkInterfaceIPConfiguration, IPAllocationMethod


class NetworkService(object):

    def create_network(self, network_client, group_name, interface_name, ip_name, region, subnet_name, network_name,
                       add_public_ip, public_ip_type, tags):
        """Create all required Azure Network components (virtual network, interface, private/public IPs)

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) resource group name (reservation id)
        :param interface_name: (str) name for Azure Network Interface resource
        :param ip_name: (str) name for Azure Public IP resource
        :param region: (str) Azure region
        :param subnet_name: (str) name for Azure Subnet resource
        :param network_name: (str) name for Azure Virtual Network resource
        :param add_public_ip: (bool) whether create Public IP resource or not
        :param public_ip_type: (str) IP Allocation method for the Public IP ("Static"/"Dynamic")
        :param tags: Azure tags
        :return: azure.mgmt.network.models.NetworkInterface instance
        """
        virtual_network = self._create_virtual_network(
            network_client=network_client,
            region=region,
            group_name=group_name,
            network_name=network_name,
            subnet_name=subnet_name,
            tags=tags)

        subnet = virtual_network.subnets[0]

        if add_public_ip:
            public_ip_address = self._create_public_ip(
                network_client=network_client,
                region=region,
                group_name=group_name,
                ip_name=ip_name,
                public_ip_type=public_ip_type,
                tags=tags)
        else:
            public_ip_address = None

        return self._create_network_interface(
            network_client=network_client,
            region=region,
            group_name=group_name,
            interface_name=interface_name,
            subnet=subnet,
            public_ip_address=public_ip_address,
            tags=tags)

    def _create_virtual_network(self, network_client, region, group_name, network_name, subnet_name, tags):
        """Create Azure Virtual Network resource

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param region: (str) Azure region
        :param group_name: (str) resource group name (reservation id)
        :param network_name: (str) name for Azure Virtual Network resource
        :param subnet_name: (str) name for Azure Subnet resource
        :param tags: Azure tags
        :return: azure.mgmt.network.models.VirtualNetwork instance
        """
        operation_poller = network_client.virtual_networks.create_or_update(
            group_name,
            network_name,
            azure.mgmt.network.models.VirtualNetwork(
                location=region,
                tags=tags,
                address_space=azure.mgmt.network.models.AddressSpace(
                    address_prefixes=[
                        '10.1.0.0/16',
                    ],
                ),
                subnets=[
                    azure.mgmt.network.models.Subnet(
                        name=subnet_name,
                        address_prefix='10.1.0.0/24')
                ],
            ),
            tags=tags
        )

        return operation_poller.result()

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

    def _create_network_interface(self, network_client, region, group_name, interface_name,
                                  subnet, public_ip_address, tags):
        """Create Azure Network Interface resource with private/public IPs

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param region: (str) Azure region
        :param group_name: (str) resource group name (reservation id)
        :param interface_name: (str) name for Azure Network Interface resource
        :param subnet: azure.mgmt.network.models.Subnet instance
        :param public_ip_address: azure.mgmt.network.models.PublicIPAddress instance
        :param tags: Azure tags
        :return: azure.mgmt.network.models.NetworkInterface instance
        """
        operation_poller = network_client.network_interfaces.create_or_update(
            group_name,
            interface_name,
            NetworkInterface(
                location=region,
                ip_configurations=[
                    NetworkInterfaceIPConfiguration(
                        name='default',
                        private_ip_allocation_method=IPAllocationMethod.dynamic,
                        subnet=subnet,
                        public_ip_address=public_ip_address
                    ),
                ],
                tags=tags
            ),
        )

        network_interface = operation_poller.result()
        private_ip_address = network_interface.ip_configurations[0].private_ip_address

        operation_poller = network_client.network_interfaces.create_or_update(
            group_name,
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

        return operation_poller.result()

    def get_public_ip(self, network_client, group_name, ip_name):
        """

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) resource group name (reservation id)
        :param ip_name: (str) name for Azure Public IP resource
        :return:
        """

        return network_client.public_ip_addresses.get(group_name, ip_name)

    def delete_nic(self, network_client, group_name, interface_name):
        """

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) resource group name (reservation id)
        :param interface_name: (str) name for Azure Network Interface resource
        :return:
        """
        network_client.network_interfaces.delete(group_name, interface_name)

    def delete_ip(self, network_client, group_name, ip_name):
        """

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) resource group name (reservation id)
        :param ip_name: (str) name for Azure Public IP resource
        :return:
        """
        network_client.public_ip_addresses.delete(group_name, ip_name)
