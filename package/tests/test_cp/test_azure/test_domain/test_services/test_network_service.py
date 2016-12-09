from unittest import TestCase

import azure
from azure.mgmt.network.models import IPAllocationMethod
from mock import MagicMock
from mock import Mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService


class TestNetworkService(TestCase):
    def setUp(self):
        self.network_service = NetworkService()

    def test_create_virtual_network(self):
        network_client = Mock(return_value=Mock())
        network_client.subnets.get = Mock(return_value="subnet")
        network_client.virtual_networks.create_or_update = Mock(return_value=Mock())
        management_group_name = Mock()
        region = Mock()
        network_name = Mock()
        subnet_name = Mock()
        vnet_cidr = Mock()
        subnet_cidr = Mock()
        network_security_group = Mock()
        tags = Mock()
        self.network_service.create_virtual_network(management_group_name=management_group_name,
                                                    network_client=network_client,
                                                    network_name=network_name,
                                                    region=region,
                                                    subnet_name=subnet_name,
                                                    tags=tags,
                                                    vnet_cidr=vnet_cidr,
                                                    subnet_cidr=subnet_cidr,
                                                    network_security_group=network_security_group)

        network_client.subnets.get.assert_called()
        network_client.virtual_networks.create_or_update.assert_called_with(management_group_name,
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
                                                                            tags=tags)

    def test_network_for_vm_fails_when_public_ip_type_is_not_correct(self):
        self.assertRaises(Exception,
                          self.network_service.create_network_for_vm,
                          network_client=MagicMock(),
                          group_name=Mock(),
                          interface_name=Mock(),
                          ip_name=Mock(),
                          region=Mock(),
                          subnet=Mock(),
                          tags=Mock(),
                          add_public_ip=True,
                          public_ip_type="a_cat")

    def test_vm_created_with_private_ip_static(self):
        # Arrange

        region = "us"
        management_group_name = "company"
        interface_name = "interface"
        network_name = "network"
        subnet_name = "subnet"
        ip_name = "ip"
        tags = "tags"

        network_client = MagicMock()
        network_client.virtual_networks.create_or_update = MagicMock()
        network_client.subnets.get = MagicMock()
        network_client.public_ip_addresses.create_or_update = MagicMock()
        network_client.public_ip_addresses.get = MagicMock()
        result = MagicMock()
        result.result().ip_configurations = [MagicMock()]
        network_client.network_interfaces.create_or_update = MagicMock(return_value=result)

        # Act
        self.network_service.create_network_for_vm(
                network_client=network_client,
                group_name=management_group_name,
                interface_name=interface_name,
                ip_name=ip_name,
                region=region,
                subnet=MagicMock(),
                add_public_ip=True,
                public_ip_type="Static",
                tags=tags)

        # Verify

        self.assertEqual(network_client.network_interfaces.create_or_update.call_count, 2)

        # first time dynamic
        self.assertEqual(network_client.network_interfaces.create_or_update.call_args_list[0][0][2].ip_configurations[
                             0].private_ip_allocation_method,
                         IPAllocationMethod.dynamic)

        # second time static
        self.assertEqual(network_client.network_interfaces.create_or_update.call_args_list[1][0][2].ip_configurations[
                             0].private_ip_allocation_method,
                         IPAllocationMethod.static)
