from unittest import TestCase

from azure.mgmt.network.models import IPAllocationMethod
from azure.mgmt.storage.models import StorageAccountCreateParameters
from mock import MagicMock
import mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.key_pair import KeyPairService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService


class TestStorageService(TestCase):
    def setUp(self):
        self.storage_service = StorageService()
        self.group_name = "test_group_name"
        self.storage_name = "teststoragename"
        self.storage_client = mock.MagicMock()

    def test_create_storage_account(self):
        # Arrange
        region = "a region"
        account_name = "account name"
        tags = {}
        group_name = "a group name"

        storage_client = MagicMock()
        storage_client.storage_accounts.create = MagicMock()
        kind_storage_value = MagicMock()
        # Act

        self.storage_service.create_storage_account(storage_client, group_name, region, account_name, tags)

        # Verify
        storage_client.storage_accounts.create.assert_called_with(group_name, account_name,
                                                                  StorageAccountCreateParameters(
                                                                      sku=MagicMock(),
                                                                      kind=kind_storage_value,
                                                                      location=region,
                                                                      tags=tags))

    def test_get_storage_account_key(self):
        """Check that method uses storage client to retrieve first access key for the storage account"""
        storage_key = mock.MagicMock()

        self.storage_client.storage_accounts.list_keys.return_value = mock.MagicMock(keys=[storage_key])

        key = self.storage_service.get_storage_account_key(
            storage_client=self.storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name)

        self.assertEqual(key, storage_key.value)


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

        network_client = MagicMock()
        network_client.virtual_networks.create_or_update = MagicMock()
        network_client.subnets.get = MagicMock()
        network_client.public_ip_addresses.create_or_update = MagicMock()
        network_client.public_ip_addresses.get = MagicMock()
        result = MagicMock()
        result.result().ip_configurations = [MagicMock()]
        network_client.network_interfaces.create_or_update = MagicMock(return_value=result)

        # Act
        self.network_service.create_network(
            network_client=network_client,
            group_name=management_group_name,
            interface_name=interface_name,
            ip_name=ip_name,
            region=region,
            subnet_name=subnet_name,
            network_name=network_name,
            add_public_ip=True,
            public_ip_type="Static",
            tags=tags)

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
        mock = MagicMock()
        compute_management_client = mock
        group_name = mock
        vm_name = mock
        region = 'a region'
        tags = {}
        compute_management_client.virtual_machines = mock
        compute_management_client.virtual_machines.create_or_update = MagicMock(return_value=mock)
        vm = 'some returned vm'
        self.vm_service._get_virtual_machine = MagicMock(return_value=vm)

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
        resource_management_client = MagicMock()
        resource_management_client.resource_groups.create_or_update = MagicMock(return_value="A test group")

        # Act
        region = 'region'
        group_name = MagicMock()
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
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        res = self.vm_service.start_vm(compute_management_client, group_name, vm_name)

        compute_management_client.virtual_machines.start.assert_called_with(resource_group_name=group_name,
                                                                            vm_name=vm_name)

        self.assertEqual(res, compute_management_client.virtual_machines.start().result())

    def test_stop_vm(self):
        """Check that method calls azure client to stop VM action and returns it result"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        res = self.vm_service.stop_vm(compute_management_client, group_name, vm_name)

        compute_management_client.virtual_machines.power_off.assert_called_with(resource_group_name=group_name,
                                                                                vm_name=vm_name)

        self.assertEqual(res, compute_management_client.virtual_machines.power_off().result())

    def test_start_vm_with_async_mode_true(self):
        """Check that method calls azure client to start VM action and doesn't wait for it result"""
        compute_management_client = MagicMock()
        operation_poller = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"
        compute_management_client.virtual_machines.power_off.return_value = operation_poller

        res = self.vm_service.start_vm(compute_management_client, group_name, vm_name, async=True)

        operation_poller.result.assert_not_called()
        self.assertIsNone(res)

    def test_stop_vm_with_async_mode_true(self):
        """Check that method calls azure client to stop VM action and doesn't wait for it result"""
        compute_management_client = MagicMock()
        operation_poller = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"
        compute_management_client.virtual_machines.power_off.return_value = operation_poller

        res = self.vm_service.stop_vm(compute_management_client, group_name, vm_name, async=True)

        operation_poller.result.assert_not_called()
        self.assertIsNone(res)


class TestKeyPairService(TestCase):
    def setUp(self):
        self.key_pair_service = KeyPairService()
        self.group_name = "test_group_name"
        self.storage_name = "teststoragename"
        self.account_key = "test_account_key"
        self.storage_client = mock.MagicMock()

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.RSA")
    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.SSHKey")
    def test_generate_key_pair(self, ssh_key_class, rsa_module):
        """Check that method uses RSA module to generate key pair and returns SSHKey model"""
        ssh_key_class.return_value = ssh_key_mock = mock.MagicMock()

        ssh_key = self.key_pair_service.generate_key_pair()

        ssh_key_class.assert_called_with(private_key=rsa_module.generate().exportKey(),
                                         public_key=rsa_module.generate().publickey().exportKey())
        self.assertIs(ssh_key, ssh_key_mock)

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.FileService")
    def test_save_key_pair(self, file_service_class):
        """Check that method uses storage client to save key pair to the Azure"""
        key_pair = mock.MagicMock()
        file_service = mock.MagicMock()
        file_service_class.return_value = file_service

        self.key_pair_service.save_key_pair(
            account_key=self.account_key,
            key_pair=key_pair,
            group_name=self.group_name,
            storage_name=self.storage_name)

        file_service_class.assert_called_once_with(account_key=self.account_key, account_name=self.storage_name)
        file_service.create_share.assert_called_once_with(self.key_pair_service.FILE_SHARE_NAME)

        file_service.create_file_from_bytes.assert_any_call(share_name=self.key_pair_service.FILE_SHARE_NAME,
                                                            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
                                                            file_name=self.key_pair_service.SSH_PUB_KEY_NAME,
                                                            file=key_pair.public_key)

        file_service.create_file_from_bytes.assert_any_call(share_name=self.key_pair_service.FILE_SHARE_NAME,
                                                            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
                                                            file_name=self.key_pair_service.SSH_PRIVATE_KEY_NAME,
                                                            file=key_pair.private_key)

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.SSHKey")
    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.FileService")
    def test_get_key_pair(self, file_service_class, ssh_key_class):
        """Check that method uses storage client to retrieve key pair from the Azure"""
        file_service = mock.MagicMock()
        file_service_class.return_value = file_service
        ssh_key_class.return_value = mocked_key_pair = mock.MagicMock()

        key_pair = self.key_pair_service.get_key_pair(
            account_key=self.account_key,
            group_name=self.group_name,
            storage_name=self.storage_name)

        file_service_class.assert_called_once_with(account_key=self.account_key, account_name=self.storage_name)

        file_service.get_file_to_bytes.assert_any_call(
            share_name=self.key_pair_service.FILE_SHARE_NAME,
            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
            file_name=self.key_pair_service.SSH_PUB_KEY_NAME)

        file_service.get_file_to_bytes.assert_any_call(
            share_name=self.key_pair_service.FILE_SHARE_NAME,
            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
            file_name=self.key_pair_service.SSH_PRIVATE_KEY_NAME)

        self.assertIs(key_pair, mocked_key_pair)
