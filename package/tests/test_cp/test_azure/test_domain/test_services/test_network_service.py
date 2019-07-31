from unittest import TestCase

import azure
from azure.mgmt.network.models import IPAllocationMethod
from mock import MagicMock
from mock import Mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService


class TestNetworkService(TestCase):
    def setUp(self):
        self.network_service = NetworkService(MagicMock(), MagicMock())
        self.network_client = Mock(return_value=Mock())

    def test_create_virtual_network(self):
        self.network_client.subnets.get = Mock(return_value="subnet")
        self.network_client.virtual_networks.create_or_update = Mock(return_value=Mock())
        management_group_name = Mock()
        region = Mock()
        network_name = Mock()
        subnet_name = Mock()
        vnet_cidr = Mock()
        subnet_cidr = Mock()
        network_security_group = Mock()
        tags = Mock()
        self.network_service.create_virtual_network(management_group_name=management_group_name,
                                                    network_client=self.network_client,
                                                    network_name=network_name,
                                                    region=region,
                                                    subnet_name=subnet_name,
                                                    tags=tags,
                                                    vnet_cidr=vnet_cidr,
                                                    subnet_cidr=subnet_cidr,
                                                    network_security_group=network_security_group)

        self.network_client.subnets.get.assert_called()
        self.network_client.virtual_networks.create_or_update.assert_called_with(management_group_name,
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
        reservation_id = 'blabla'
        cloudshell_session = MagicMock()

        network_client = MagicMock()
        network_client.virtual_networks.create_or_update = MagicMock()
        network_client.subnets.get = MagicMock()
        network_client.public_ip_addresses.create_or_update = MagicMock()
        network_client.public_ip_addresses.get = MagicMock()
        result = MagicMock()
        result.result().ip_configurations = [MagicMock()]
        network_client.network_interfaces.create_or_update = MagicMock(return_value=result)
        cloud_provider_model = MagicMock()
        cloud_provider_model.private_ip_allocation_method = 'cloudshell allocation'
        sandbox_virtual_network = MagicMock()
        sandbox_virtual_network.name = "sandbox"
        self.network_service.get_sandbox_virtual_network = MagicMock(sandbox_virtual_network)

        # Act
        self.network_service.create_network_for_vm(
            network_client=network_client,
            group_name=management_group_name,
            interface_name=interface_name,
            ip_name=ip_name,
            cloud_provider_model=cloud_provider_model,
            subnet=MagicMock(),
            add_public_ip=True,
            public_ip_type="Static",
            tags=tags,
            logger=MagicMock(),
            reservation_id=reservation_id,
            cloudshell_session=cloudshell_session)

        # Verify

        self.assertEqual(network_client.network_interfaces.create_or_update.call_count, 1)

        # one time static
        self.assertEqual(network_client.network_interfaces.create_or_update.call_args_list[0][0][2].ip_configurations[0]
                         .private_ip_allocation_method, IPAllocationMethod.static)

    def test_delete_subnet(self):
        """Check that method will use network_client to delete subnet and will wait until deletion will be done"""
        group_name = "test_group_name"
        vnet_name = "test_vnet_name"
        subnet_name = "test_subnet_name"
        operation_poller = MagicMock()
        self.network_client.subnets.delete.return_value = operation_poller

        # Act
        self.network_service.delete_subnet(network_client=self.network_client,
                                           group_name=group_name,
                                           vnet_name=vnet_name,
                                           subnet_name=subnet_name)

        # Verify
        self.network_client.subnets.delete.assert_called_once_with(resource_group_name=group_name,
                                                                   virtual_network_name=vnet_name,
                                                                   subnet_name=subnet_name)
        operation_poller.wait.assert_called_once_with()
