import azure
from azure.mgmt.network.models import NetworkInterface, NetworkInterfaceIPConfiguration, IPAllocationMethod


class NetworkService(object):
    def __init__(self):
        pass

    def create_network(self, network_client, group_name, interface_name, ip_name, region, subnet_name, network_name):
        nic_id = self.create_network_interface(
            network_client,
            region,
            group_name,
            interface_name,
            network_name,
            subnet_name,
            ip_name)
        return nic_id

    def create_network_interface(self,
                                 network_client,
                                 region,
                                 management_group_name,
                                 interface_name,
                                 network_name,
                                 subnet_name,
                                 ip_name):
        result = network_client.virtual_networks.create_or_update(
            management_group_name,
            network_name,
            azure.mgmt.network.models.VirtualNetwork(
                location=region,
                address_space=azure.mgmt.network.models.AddressSpace(
                    address_prefixes=[
                        '10.1.0.0/16',
                    ],
                ),
                subnets=[
                    azure.mgmt.network.models.Subnet(
                        name=subnet_name,
                        address_prefix='10.1.0.0/24',
                    ),
                ],
            ),
        )

        result.wait()

        subnet = network_client.subnets.get(management_group_name, network_name, subnet_name)

        result = network_client.public_ip_addresses.create_or_update(
            management_group_name,
            ip_name,
            azure.mgmt.network.models.PublicIPAddress(
                location=region,
                public_ip_allocation_method=azure.mgmt.network.models.IPAllocationMethod.dynamic,
                idle_timeout_in_minutes=4,
            ),
        )

        result.wait()

        public_ip_address = network_client.public_ip_addresses.get(management_group_name, ip_name)
        public_ip_id = public_ip_address.id

        result = network_client.network_interfaces.create_or_update(
            management_group_name,
            interface_name,
            NetworkInterface(
                location=region,
                ip_configurations=[
                    NetworkInterfaceIPConfiguration(
                        name='default',
                        private_ip_allocation_method=IPAllocationMethod.static,
                        subnet=subnet,
                        public_ip_address=azure.mgmt.network.models.PublicIPAddress(
                            id=public_ip_id,
                        ),
                    ),
                ],
            ),
        )

        result.wait()

        network_interface = network_client.network_interfaces.get(
            management_group_name,
            interface_name,
        )

        return network_interface.id

    def get_public_ip(self, network_client, group_name, ip_name):
        """

        :param network_client:
        :param group_name:
        :param ip_name:
        :return:
        """

        return network_client.public_ip_addresses.get(group_name, ip_name)
