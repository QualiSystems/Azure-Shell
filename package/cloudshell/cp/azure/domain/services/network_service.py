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
                              tags):
        """
        This method creates a an ip address and a nic for the vm
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
        public_ip_address = self.create_public_ip_address(ip_name, group_name, network_client, region, tags)
        public_ip_id = public_ip_address.id

        # 2. Create NIC
        result = self.create_nic(interface_name,
                                 group_name,
                                 network_client,
                                 public_ip_id,
                                 region,
                                 subnet,
                                 IPAllocationMethod.dynamic,
                                 tags)

        # 3. update the type of private ip from dynamic to static (ip itself must be supplied)
        private_ip_address = result.result().ip_configurations[0].private_ip_address
        self.create_nic_with_private_ip(interface_name,
                                        group_name,
                                        network_client,
                                        private_ip_address,
                                        public_ip_id,
                                        region,
                                        subnet,
                                        tags)

        network_interface = network_client.network_interfaces.get(
            group_name,
            interface_name,
        )

        return network_interface.id

    def create_nic_with_private_ip(self, interface_name, management_group_name, network_client, private_ip_address,
                                   public_ip_id, region, subnet, tags):
        """

        :param interface_name:
        :param management_group_name:
        :param network_client:
        :param private_ip_address:
        :param public_ip_id:
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
                        public_ip_address=azure.mgmt.network.models.PublicIPAddress(
                            id=public_ip_id,
                        ),
                    ),
                ],
                tags=tags
            ),
        )
        result.wait()

    def create_nic(self, interface_name, management_group_name, network_client, public_ip_id, region, subnet,
                   private_ip_allocation_method, tags):
        """

        :param interface_name:
        :param management_group_name:
        :param network_client:
        :param public_ip_id:
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
                        public_ip_address=azure.mgmt.network.models.PublicIPAddress(
                            id=public_ip_id,
                        ),
                    ),
                ],
                tags=tags
            ),
        )
        result.wait()
        return result

    def create_public_ip_address(self, ip_name, management_group_name, network_client, region, tags):
        """

        :param ip_name:
        :param management_group_name:
        :param network_client:
        :param region:
        :param tags:
        :return:
        """
        result = network_client.public_ip_addresses.create_or_update(
            management_group_name,
            ip_name,
            azure.mgmt.network.models.PublicIPAddress(
                location=region,
                public_ip_allocation_method=azure.mgmt.network.models.IPAllocationMethod.static,
                idle_timeout_in_minutes=4,
                tags=tags
            ),
        )
        result.wait()
        public_ip_address = network_client.public_ip_addresses.get(management_group_name, ip_name)
        return public_ip_address

    def create_virtual_network(self, management_group_name,
                               network_client, network_name,
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
        network_client.network_interfaces.delete(group_name, interface_name)

    def delete_ip(self, network_client, group_name, ip_name):
        """

        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name:
        :param ip_name:
        :return:
        """
        network_client.public_ip_addresses.delete(group_name, ip_name)

    def get_virtual_networks(self, network_client, group_name):
        """

        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param group_name:
        :return:
        """
        networks_list = network_client.virtual_networks.list(group_name)
        return list(networks_list)

