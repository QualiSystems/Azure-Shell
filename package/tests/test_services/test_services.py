from unittest import TestCase

from azure.mgmt.network.models import IPAllocationMethod
from azure.mgmt.storage.models import StorageAccountCreateParameters
from mock import MagicMock
import mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.key_pair import KeyPairService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.services.vm_credentials_service import VMCredentialsService
from cloudshell.cp.azure.models.vm_credentials import VMCredentials


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
                                                                      tags=tags),
                                                                  raw=False)

    def test_get_storage_account_key(self):
        """Check that method uses storage client to retrieve first access key for the storage account"""
        storage_key = mock.MagicMock()

        self.storage_client.storage_accounts.list_keys.return_value = mock.MagicMock(keys=[storage_key])

        key = self.storage_service._get_storage_account_key(
            storage_client=self.storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name)

        self.assertEqual(key, storage_key.value)

    @mock.patch("cloudshell.cp.azure.domain.services.storage_service.FileService")
    def test_get_file_service(self, file_service_class):
        """Check that method will return FileService instance"""
        file_service_class.return_value = mocked_file_service = MagicMock()
        mocked_account_key = MagicMock()
        self.storage_service._get_storage_account_key = MagicMock(return_value=mocked_account_key)

        # Act
        file_service = self.storage_service._get_file_service(storage_client=self.storage_client,
                                                              group_name=self.group_name,
                                                              storage_name=self.storage_name)

        # Verify
        self.storage_service._get_storage_account_key.assert_called_once_with(storage_client=self.storage_client,
                                                                              group_name=self.group_name,
                                                                              storage_name=self.storage_name)

        file_service_class.assert_called_once_with(account_name=self.storage_name, account_key=mocked_account_key)
        self.assertEqual(file_service, mocked_file_service)

    def test_create_file(self):
        """Check that method uses storage client to save file to the Azure"""
        share_name = "testsharename"
        directory_name = "testdirectory"
        file_name = "testfilename"
        file_content = MagicMock()
        file_service = MagicMock()
        self.storage_service._get_file_service = MagicMock(return_value=file_service)

        # Act
        self.storage_service.create_file(storage_client=self.storage_client,
                                         group_name=self.group_name,
                                         storage_name=self.storage_name,
                                         share_name=share_name,
                                         directory_name=directory_name,
                                         file_name=file_name,
                                         file_content=file_content)

        # Verify
        file_service.create_share.assert_called_once_with(share_name=share_name, fail_on_exist=False)
        file_service.create_file_from_bytes.assert_called_once_with(share_name=share_name,
                                                                    directory_name=directory_name,
                                                                    file_name=file_name,
                                                                    file=file_content)

    def test_get_key_pair(self):
        """Check that method uses storage client to retrieve file from the Azure"""
        share_name = "testsharename"
        directory_name = "testdirectory"
        file_name = "testfilename"
        file_service = MagicMock()
        mocked_file = MagicMock()
        file_service.get_file_to_bytes.return_value = mocked_file
        self.storage_service._get_file_service = MagicMock(return_value=file_service)

        # Act
        azure_file = self.storage_service.get_file(storage_client=self.storage_client,
                                                   group_name=self.group_name,
                                                   storage_name=self.storage_name,
                                                   share_name=share_name,
                                                   directory_name=directory_name,
                                                   file_name=file_name)

        # Verify
        file_service.get_file_to_bytes.assert_called_once_with(share_name=share_name,
                                                               directory_name=directory_name,
                                                               file_name=file_name)
        self.assertEqual(azure_file, mocked_file)


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
                                  vm_credentials=MagicMock(),
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

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.LinuxConfiguration")
    def test_prepare_linux_configuration(self, linux_configuration_class):
        """Check that method will return LinuxConfiguration instance for the Azure client"""
        ssh_key = mock.MagicMock()
        linux_configuration = mock.MagicMock()
        linux_configuration_class.return_value = linux_configuration

        res = self.vm_service._prepare_linux_configuration(ssh_key)

        self.assertIs(res, linux_configuration)

    def test_get_image_operation_system(self):
        """Check that method returns operating_system of the provided image"""
        compute_client = mock.MagicMock()
        image = mock.MagicMock()
        compute_client.virtual_machine_images.get.return_value = image

        os_type = self.vm_service.get_image_operation_system(
            compute_management_client=compute_client,
            location=mock.MagicMock(),
            publisher_name=mock.MagicMock(),
            offer=mock.MagicMock(),
            skus=mock.MagicMock())

        compute_client.virtual_machine_images.list.assert_called_once()
        compute_client.virtual_machine_images.get.assert_called_once()
        self.assertEqual(os_type, image.os_disk_image.operating_system)


class TestVMCredentialsService(TestCase):
    def setUp(self):
        self.test_username = "test_username"
        self.test_password = "testPassword123"
        self.test_group_name = "test_username"
        self.test_storage_name = "test_storage_name"
        self.test_storage_service = mock.MagicMock()
        self.test_key_pair_service = mock.MagicMock()
        self.test_storage_client = mock.MagicMock()
        self.vm_credentials = VMCredentialsService()

    def test_generate_password(self):
        """Check that method will generate password with given length"""
        password = self.vm_credentials._generate_password(19)
        self.assertEqual(len(password), 19)

    @mock.patch("cloudshell.cp.azure.domain.services.vm_credentials_service.AuthorizedKey")
    def test_get_ssh_key(self, authorized_key_class):
        """Check that method will return cloudshell.cp.azure.models.authorized_key.AuthorizedKey instance"""
        authorized_key_class.return_value = authorized_key = mock.MagicMock()

        ssh_key = self.vm_credentials._get_ssh_key(
            username=self.test_username,
            storage_service=self.test_storage_service,
            key_pair_service=self.test_key_pair_service,
            storage_client=self.test_storage_client,
            group_name=self.test_group_name,
            storage_name=self.test_storage_name)

        self.assertIs(ssh_key, authorized_key)

    @mock.patch("cloudshell.cp.azure.domain.services.vm_credentials_service.OperatingSystemTypes")
    def test_prepare_credentials_with_windows_os_type(self, os_types):
        """Check that method will call _prepare_windows_credentials and return VMCredentials model instance"""
        self.vm_credentials._prepare_windows_credentials = mock.MagicMock(return_value=(self.test_username,
                                                                                        self.test_password))

        vm_creds = self.vm_credentials.prepare_credentials(
            os_type=os_types.windows,
            username=self.test_username,
            password=self.test_password,
            storage_service=self.test_storage_service,
            key_pair_service=self.test_key_pair_service,
            storage_client=self.test_storage_client,
            group_name=self.test_group_name,
            storage_name=self.test_storage_name)

        self.vm_credentials._prepare_windows_credentials.assert_called_once_with(self.test_username, self.test_password)
        self.assertIsInstance(vm_creds, VMCredentials)

    @mock.patch("cloudshell.cp.azure.domain.services.vm_credentials_service.OperatingSystemTypes")
    def test_prepare_credentials_with_linux_os_type(self, os_types):
        """Check that method will call _prepare_linux_credentials and return VMCredentials model instance"""
        # from azure.mgmt.compute.models import OperatingSystemTypes
        self.vm_credentials._prepare_linux_credentials = mock.MagicMock(return_value=(self.test_username,
                                                                                      self.test_password,
                                                                                      mock.MagicMock()))
        vm_creds = self.vm_credentials.prepare_credentials(
            os_type=os_types.linux,
            username=self.test_username,
            password=self.test_password,
            storage_service=self.test_storage_service,
            key_pair_service=self.test_key_pair_service,
            storage_client=self.test_storage_client,
            group_name=self.test_group_name,
            storage_name=self.test_storage_name)

        self.vm_credentials._prepare_linux_credentials.assert_called_once_with(
            username=self.test_username,
            password=self.test_password,
            storage_service=self.test_storage_service,
            key_pair_service=self.test_key_pair_service,
            storage_client=self.test_storage_client,
            group_name=self.test_group_name,
            storage_name=self.test_storage_name)

        self.assertIsInstance(vm_creds, VMCredentials)

    def test_prepare_windows_credentials(self):
        """Check that method will return same credentials if username and password were provided"""
        username, password = self.vm_credentials._prepare_windows_credentials(self.test_username, self.test_password)

        self.assertEqual(username, self.test_username)
        self.assertEqual(password, self.test_password)

    def test_prepare_windows_credentials_without_user_and_password(self):
        """Check that method will return default username and generate password if credentials weren't provided"""
        generated_pass = mock.MagicMock()
        self.vm_credentials._generate_password = mock.MagicMock(return_value=generated_pass)

        username, password = self.vm_credentials._prepare_windows_credentials("", "")

        self.assertEqual(username, self.vm_credentials.DEFAULT_WINDOWS_USERNAME)
        self.assertEqual(password, generated_pass)

    def test_prepare_linux_credentials(self):
        """Check that method will return same credentials if username and password were provided"""
        username, password, ssh_key = self.vm_credentials._prepare_linux_credentials(
            username=self.test_username,
            password=self.test_password,
            storage_service=self.test_storage_service,
            key_pair_service=self.test_key_pair_service,
            storage_client=self.test_storage_client,
            group_name=self.test_group_name,
            storage_name=self.test_storage_name)

        self.assertEqual(username, self.test_username)
        self.assertEqual(password, self.test_password)
        self.assertIsNone(ssh_key)

    def test_prepare_linux_credentials_without_user_and_password(self):
        """Check that method will return default username and ssh_key if credentials weren't provided"""
        returned_ssh_key = mock.MagicMock()
        self.vm_credentials._get_ssh_key = mock.MagicMock(return_value=returned_ssh_key)

        username, password, ssh_key = self.vm_credentials._prepare_linux_credentials(
            username="",
            password="",
            storage_service=self.test_storage_service,
            key_pair_service=self.test_key_pair_service,
            storage_client=self.test_storage_client,
            group_name=self.test_group_name,
            storage_name=self.test_storage_name)

        self.assertEqual(username, self.vm_credentials.DEFAULT_LINUX_USERNAME)
        self.assertEqual(password, "")
        self.assertEqual(ssh_key, returned_ssh_key)


class TestKeyPairService(TestCase):
    def setUp(self):
        self.group_name = "test_group_name"
        self.storage_name = "teststoragename"
        self.account_key = "test_account_key"
        self.storage_service = MagicMock()
        self.key_pair_service = KeyPairService(storage_service=self.storage_service)

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.RSA")
    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.SSHKey")
    def test_generate_key_pair(self, ssh_key_class, rsa_module):
        """Check that method uses RSA module to generate key pair and returns SSHKey model"""
        ssh_key_class.return_value = ssh_key_mock = mock.MagicMock()

        ssh_key = self.key_pair_service.generate_key_pair()

        ssh_key_class.assert_called_with(private_key=rsa_module.generate().exportKey(),
                                         public_key=rsa_module.generate().publickey().exportKey())
        self.assertIs(ssh_key, ssh_key_mock)

    def test_save_key_pair(self):
        """Check that method uses storage service to save key pair to the Azure"""
        key_pair = MagicMock()
        storage_client = MagicMock()

        # Act
        self.key_pair_service.save_key_pair(
            storage_client=storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name,
            key_pair=key_pair)

        # Verify
        self.key_pair_service._storage_service.create_file.assert_any_call(
            storage_client=storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name,
            share_name=self.key_pair_service.FILE_SHARE_NAME,
            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
            file_name=self.key_pair_service.SSH_PUB_KEY_NAME,
            file_content=key_pair.public_key)

        self.key_pair_service._storage_service.create_file.assert_any_call(
            storage_client=storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name,
            share_name=self.key_pair_service.FILE_SHARE_NAME,
            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
            file_name=self.key_pair_service.SSH_PRIVATE_KEY_NAME,
            file_content=key_pair.private_key)

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.SSHKey")
    def test_get_key_pair(self, ssh_key_class):
        """Check that method uses storage service to retrieve key pair from the Azure"""
        storage_client = MagicMock()
        mocked_ssh_key = MagicMock()
        ssh_key_class.return_value = mocked_ssh_key

        # Act
        key_pair = self.key_pair_service.get_key_pair(
            storage_client=storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name)

        # Verify
        self.key_pair_service._storage_service.get_file.assert_any_call(
            storage_client=storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name,
            share_name=self.key_pair_service.FILE_SHARE_NAME,
            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
            file_name=self.key_pair_service.SSH_PUB_KEY_NAME)

        self.key_pair_service._storage_service.get_file.assert_any_call(
            storage_client=storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name,
            share_name=self.key_pair_service.FILE_SHARE_NAME,
            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
            file_name=self.key_pair_service.SSH_PRIVATE_KEY_NAME)

        self.assertEqual(key_pair, mocked_ssh_key)
