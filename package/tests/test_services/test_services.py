from unittest import TestCase

from azure.mgmt.network.models import IPAllocationMethod
from azure.mgmt.storage.models import StorageAccountCreateParameters
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from mock import Mock


class TestStorageService(TestCase):
    def setUp(self):
        self.storage_service = StorageService()

    def test_create_storage_account(self):
        # Arrange
        region = "a region"
        account_name = "account name"
        tags = {}
        group_name = "a group name"

        storage_client = Mock()
        storage_client.storage_accounts.create = Mock(return_value=Mock())
        kind_storage_value = Mock()
        # Act

        self.storage_service.create_storage_account(storage_client, group_name, region, account_name, tags)

        # Verify
        storage_client.storage_accounts.create.assert_called_with(group_name, account_name,
                                                                  StorageAccountCreateParameters(
                                                                      sku=Mock(),
                                                                      kind=kind_storage_value,
                                                                      location=region,
                                                                      tags=tags))


class TestNetworkService(TestCase):
    def setUp(self):
        self.network_service = NetworkService()

    def test_vm_created_with_private_ip_static(self):
        # Arrange

        region = "us"
        management_group_name = "company"
        interface_name = "interface"
        network_name = "network"
        subnet_name = "subnet"
        ip_name = "ip"
        tags = "tags"

        network_client = Mock()
        network_client.virtual_networks.create_or_update = Mock()
        network_client.subnets.get = Mock()
        network_client.public_ip_addresses.create_or_update = Mock()
        network_client.public_ip_addresses.get = Mock()
        result = Mock()
        result.result().ip_configurations = [Mock()]
        network_client.network_interfaces.create_or_update = Mock(return_value=result)

        # Act

        self.network_service.create_network_interface(network_client, region, management_group_name,
                                                      interface_name, network_name, subnet_name,
                                                      ip_name, tags)

        # Verify

        self.assertEqual(network_client.network_interfaces.create_or_update.call_count, 2)

        # first time dynamic
        self.assertEqual(network_client.network_interfaces.create_or_update.call_args_list[0][0][2].ip_configurations[0].private_ip_allocation_method,
                         IPAllocationMethod.dynamic)

        # second time static
        self.assertEqual(network_client.network_interfaces.create_or_update.call_args_list[1][0][2].ip_configurations[0].private_ip_allocation_method,
                         IPAllocationMethod.static)


class TestVMService(TestCase):
    def setUp(self):
        self.vm_service = VirtualMachineService()

    def test_vm_service_create_vm(self):
        mock = Mock()
        compute_management_client = mock
        group_name = mock
        vm_name = mock
        region = 'a region'
        tags = {}
        compute_management_client.virtual_machines = mock
        compute_management_client.virtual_machines.create_or_update = Mock(return_value=mock)
        vm = 'some returned vm'
        self.vm_service._get_virtual_machine = Mock(return_value=vm)

        # Act
        self.vm_service.create_vm(compute_management_client=compute_management_client,
                                  image_offer=mock,
                                  image_publisher=mock,
                                  image_sku=mock,
                                  image_version=mock,
                                  admin_password=mock,
                                  admin_username=mock,
                                  computer_name=mock,
                                  group_name=group_name,
                                  nic_id=mock,
                                  region=region,
                                  storage_name=mock,
                                  vm_name=vm_name,
                                  tags=tags,
                                  instance_type=mock)

        # Verify
        compute_management_client.virtual_machines.create_or_update.assert_called_with(group_name, vm_name, vm)

    def test_vm_service_create_resource_group(self):
        # Arrange
        resource_management_client = Mock()
        resource_management_client.resource_groups.create_or_update = Mock(return_value="A test group")

        # Act
        region = 'region'
        group_name = Mock()
        tags = {}
        self.vm_service.create_resource_group(resource_management_client=resource_management_client,
                                              region=region,
                                              group_name=group_name, tags=tags)

        # Verify
        from azure.mgmt.resource.resources.models import ResourceGroup
        resource_management_client.resource_groups.create_or_update(group_name,
                                                                    ResourceGroup(location=region, tags=tags))

    def test_start_vm(self):
        """Check that method calls azure client to start VM action and returns it result"""
        compute_management_client = Mock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        res = self.vm_service.start_vm(compute_management_client, group_name, vm_name)

        compute_management_client.virtual_machines.start.assert_called_with(resource_group_name=group_name,
                                                                            vm_name=vm_name)

        self.assertEqual(res, compute_management_client.virtual_machines.start().result())

    def test_stop_vm(self):
        """Check that method calls azure client to stop VM action and returns it result"""
        compute_management_client = Mock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        res = self.vm_service.stop_vm(compute_management_client, group_name, vm_name)

        compute_management_client.virtual_machines.power_off.assert_called_with(resource_group_name=group_name,
                                                                                vm_name=vm_name)

        self.assertEqual(res, compute_management_client.virtual_machines.power_off().result())

    def test_start_vm_with_async_mode_true(self):
        """Check that method calls azure client to start VM action and doesn't wait for it result"""
        compute_management_client = Mock()
        operation_poller = Mock()
        group_name = "test_group_name"
        vm_name = "test_group_name"
        compute_management_client.virtual_machines.power_off.return_value = operation_poller

        res = self.vm_service.start_vm(compute_management_client, group_name, vm_name, async=True)

        operation_poller.result.assert_not_called()
        self.assertIsNone(res)

    def test_stop_vm_with_async_mode_true(self):
        """Check that method calls azure client to stop VM action and doesn't wait for it result"""
        compute_management_client = Mock()
        operation_poller = Mock()
        group_name = "test_group_name"
        vm_name = "test_group_name"
        compute_management_client.virtual_machines.power_off.return_value = operation_poller

        res = self.vm_service.stop_vm(compute_management_client, group_name, vm_name, async=True)

        operation_poller.result.assert_not_called()
        self.assertIsNone(res)
