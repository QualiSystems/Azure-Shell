from unittest import TestCase

import azure
import mock
from azure.mgmt.network.models import IPAllocationMethod, NetworkSecurityGroup, SecurityRule
from azure.mgmt.storage.models import StorageAccountCreateParameters
from mock import MagicMock
from mock import Mock
from msrestazure.azure_operation import AzureOperationPoller

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.key_pair import KeyPairService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.services.vm_credentials_service import VMCredentialsService
from cloudshell.cp.azure.models.vm_credentials import VMCredentials
from cloudshell.cp.azure.domain.services.security_group import SecurityGroupService
from tests.helpers.test_helper import TestHelper


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

    def test_create_storage_account_wait_for_result(self):
        # Arrange
        storage_accounts_create = AzureOperationPoller(Mock(), Mock(), Mock())
        storage_accounts_create.wait = Mock()
        storage_client = MagicMock()
        storage_client.storage_accounts.create = Mock(return_value=storage_accounts_create)
        region = "a region"
        account_name = "account name"
        tags = {}
        group_name = "a group name"
        wait_until_created = True

        # Act
        self.storage_service.create_storage_account(storage_client, group_name, region, account_name, tags,
                                                    wait_until_created)

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(storage_accounts_create.wait))

    def test_get_storage_per_resource_group(self):
        # Arrange
        storage_client = Mock()
        group_name = "a group name"
        storage_client.storage_accounts.list_by_resource_group = Mock(return_value=[])

        # Act
        result = self.storage_service.get_storage_per_resource_group(
            storage_client,
            group_name
        )

        # Verify
        self.assertTrue(isinstance(result, list))

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
        expected_cached_key = (self.group_name, self.storage_name)
        self.assertIn(expected_cached_key, self.storage_service._cached_file_services)
        self.assertEqual(file_service, self.storage_service._cached_file_services[expected_cached_key])

    @mock.patch("cloudshell.cp.azure.domain.services.storage_service.BlockBlobService")
    def test_get_blob_service(self, blob_service_class):
        """Check that method will return BlockBlobService instance"""
        blob_service_class.return_value = mocked_blob_service = MagicMock()
        mocked_account_key = MagicMock()
        self.storage_service._get_storage_account_key = MagicMock(return_value=mocked_account_key)

        # Act
        blob_service = self.storage_service._get_blob_service(storage_client=self.storage_client,
                                                              group_name=self.group_name,
                                                              storage_name=self.storage_name)

        # Verify
        self.storage_service._get_storage_account_key.assert_called_once_with(storage_client=self.storage_client,
                                                                              group_name=self.group_name,
                                                                              storage_name=self.storage_name)

        blob_service_class.assert_called_once_with(account_name=self.storage_name, account_key=mocked_account_key)

        self.assertEqual(blob_service, mocked_blob_service)
        expected_cached_key = (self.group_name, self.storage_name)
        self.assertIn(expected_cached_key, self.storage_service._cached_blob_services)
        self.assertEqual(blob_service, self.storage_service._cached_blob_services[expected_cached_key])

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

    @mock.patch("cloudshell.cp.azure.domain.services.storage_service.AzureBlobUrlModel")
    def test_parse_blob_url(self, blob_url_model_class):
        """Check that method will parse Azure blob URL into AzureBlobUrl model"""
        storage_account_name = "testaccount"
        container_name = "testcontainer"
        blob_name = "testblobname"
        blob_url = "https://{}.blob.core.windows.net/{}/{}".format(storage_account_name, container_name, blob_name)
        expected_blob_url_model = MagicMock()
        blob_url_model_class.return_value = expected_blob_url_model

        # Act
        blob_url_model = self.storage_service.parse_blob_url(blob_url=blob_url)

        # Verify
        self.assertEqual(blob_url_model, expected_blob_url_model)
        blob_url_model_class.assert_called_once_with(blob_name=blob_name,
                                                     container_name=container_name,
                                                     storage_name=storage_account_name)

    def test_wait_until_blob_copied_ends_with_success_status(self):
        """Check that method will stop infinite loop if Blob copy operation ended with the success status"""
        container_name = "testcontainer"
        blob_name = "testblobname"
        blob_service = MagicMock()
        blob = MagicMock()
        blob.properties.copy.status = "success"
        blob_service.get_blob_properties.return_value = blob

        # Act
        self.storage_service._wait_until_blob_copied(
            blob_service=blob_service,
            container_name=container_name,
            blob_name=blob_name)

        # Verify
        blob_service.get_blob_properties.assert_called_once_with(container_name, blob_name)

    def test_wait_until_blob_copied_ends_with_failed_status(self):
        """Check that method will raise Exception if Blob copy operation ended with the failed status"""
        container_name = "testcontainer"
        blob_name = "testblobname"
        blob_service = MagicMock()
        blob = MagicMock()
        blob.properties.copy.status = "failed"
        blob_service.get_blob_properties.return_value = blob

        with self.assertRaises(Exception):
            self.storage_service._wait_until_blob_copied(
                blob_service=blob_service,
                container_name=container_name,
                blob_name=blob_name)

    def test_wait_until_blob_copied_will_wait_for_operation(self):
        """Check that method will continue loop if Blob copy operation is in copying status"""
        container_name = "testcontainer"
        blob_name = "testblobname"
        blob_service = MagicMock()
        blob = MagicMock()
        blob.properties.copy.status = "copying"
        blob_service.get_blob_properties.return_value = blob
        sleep_time = 5

        class ExitLoopException(Exception):
            """Exception for existing infinite loop"""
            pass

        with mock.patch("cloudshell.cp.azure.domain.services.storage_service.time.sleep",
                        side_effect=ExitLoopException) as sleep:

            with self.assertRaises(ExitLoopException):
                self.storage_service._wait_until_blob_copied(
                    blob_service=blob_service,
                    container_name=container_name,
                    blob_name=blob_name,
                    sleep_time=sleep_time)

            # Verify
            sleep.assert_called_once_with(sleep_time)

    def test__copy_blob_file_already_exists(self):
        """Check that method will not copy Blob if such one already exists under the storage/container"""
        group_name_copy_from = "testgroupcopyfrom"
        group_name_copy_to = "testgroupcopyto"
        storage_client = MagicMock()
        ulr_model_copy_from = MagicMock()
        url_model_copy_to = MagicMock()
        expected_url = "https://teststorage.blob.core.windows.net/testcontainer/testblob"
        blob_service = MagicMock()
        blob_service.exists.return_value = True
        blob_service.make_blob_url.return_value = expected_url
        self.storage_service._get_blob_service = MagicMock(return_value=blob_service)
        self.storage_service._wait_until_blob_copied = MagicMock()

        # Act
        blob_url = self.storage_service._copy_blob(storage_client=storage_client,
                                                   group_name_copy_from=group_name_copy_from,
                                                   group_name_copy_to=group_name_copy_to,
                                                   ulr_model_copy_from=ulr_model_copy_from,
                                                   url_model_copy_to=url_model_copy_to)

        # Verify
        blob_service.exists.assert_called_once_with(blob_name=url_model_copy_to.blob_name,
                                                    container_name=url_model_copy_to.container_name)

        blob_service.create_container.assert_not_called()
        blob_service.copy_blob.assert_not_called()
        self.storage_service._wait_until_blob_copied.assert_not_called()
        self.assertEqual(blob_url, expected_url)

    def test__copy_blob_file_start_copy_operation(self):
        """Check that method will copy Blob if such one is not present under the storage/container"""
        group_name_copy_from = "testgroupcopyfrom"
        group_name_copy_to = "testgroupcopyto"
        storage_client = MagicMock()
        ulr_model_copy_from = MagicMock()
        url_model_copy_to = MagicMock()
        expected_url = "https://teststorage.blob.core.windows.net/testcontainer/testblob"
        blob_service = MagicMock()
        blob_service.exists.return_value = False
        blob_service.make_blob_url.return_value = expected_url
        self.storage_service._get_blob_service = MagicMock(return_value=blob_service)
        self.storage_service._wait_until_blob_copied = MagicMock()

        # Act
        blob_url = self.storage_service._copy_blob(storage_client=storage_client,
                                                   group_name_copy_from=group_name_copy_from,
                                                   group_name_copy_to=group_name_copy_to,
                                                   ulr_model_copy_from=ulr_model_copy_from,
                                                   url_model_copy_to=url_model_copy_to)

        # Verify
        blob_service.exists.assert_called_once_with(blob_name=url_model_copy_to.blob_name,
                                                    container_name=url_model_copy_to.container_name)

        blob_service.create_container.assert_called_once_with(container_name=url_model_copy_to.container_name,
                                                              fail_on_exist=False)

        blob_service.copy_blob.assert_called_once_with(blob_name=url_model_copy_to.blob_name,
                                                       container_name=url_model_copy_to.container_name,
                                                       copy_source=expected_url)

        self.storage_service._wait_until_blob_copied.assert_called_once_with(
            blob_name=url_model_copy_to.blob_name,
            container_name=url_model_copy_to.container_name,
            blob_service=blob_service)

        self.assertEqual(blob_url, expected_url)

    @mock.patch("cloudshell.cp.azure.domain.services.storage_service.BlobCopyOperationState")
    def test_copy_blob_retuns_blob_url_from_cache(self, blob_copying_state):
        """Check that method will return copied Blob URL from the cache if file was already copied"""
        group_name_copy_from = "test_group_copy_from"
        group_name_copy_to = "test_group_copy_to"
        storage_name_copy_to = "test_storage_name_copy_to"
        container_name_copy_to = "test_container_name_copy_to"
        blob_name_copy_to = "test_blob_name_copy_to"
        source_copy_from = "https://teststoragesourse.blob.core.windows.net/testsourcecontainer/testsourceblob"
        expected_blob_url = "https://teststorage.blob.core.windows.net/testcontainer/testblob"
        storage_client = MagicMock()
        self.storage_service._copy_blob = MagicMock()

        cache_key = (storage_name_copy_to, container_name_copy_to, blob_name_copy_to)
        self.storage_service._cached_copied_blob_urls = {
            cache_key: {
                "state": blob_copying_state.success,
                "result": expected_blob_url
            }
        }

        # Act
        blob_url = self.storage_service.copy_blob(storage_client=storage_client,
                                                  group_name_copy_from=group_name_copy_from,
                                                  storage_name_copy_to=storage_name_copy_to,
                                                  container_name_copy_to=container_name_copy_to,
                                                  blob_name_copy_to=blob_name_copy_to,
                                                  source_copy_from=source_copy_from,
                                                  group_name_copy_to=group_name_copy_to)

        # Verify
        self.assertEqual(blob_url, expected_blob_url)
        self.storage_service._copy_blob.assert_not_called()

    @mock.patch("cloudshell.cp.azure.domain.services.storage_service.AzureBlobUrlModel")
    def test_copy_blob_start_execute_copy_operation(self, blob_model_class):
        """Check that method will execute copy operation"""
        group_name_copy_from = "test_group_copy_from"
        group_name_copy_to = "test_group_copy_to"
        storage_name_copy_to = "test_storage_name_copy_to"
        container_name_copy_to = "test_container_name_copy_to"
        blob_name_copy_to = "test_blob_name_copy_to"
        source_copy_from = "https://teststoragesourse.blob.core.windows.net/testsourcecontainer/testsourceblob"
        expected_blob_url = "https://teststorage.blob.core.windows.net/testcontainer/testblob"
        storage_client = MagicMock()
        self.storage_service._copy_blob = MagicMock(return_value=expected_blob_url)
        blob_model_copy_to = MagicMock()
        blob_model_class.return_value = blob_model_copy_to
        blob_model_copy_from = MagicMock()
        self.storage_service.parse_blob_url = MagicMock(return_value=blob_model_copy_from)

        # Act
        blob_url = self.storage_service.copy_blob(storage_client=storage_client,
                                                  group_name_copy_from=group_name_copy_from,
                                                  storage_name_copy_to=storage_name_copy_to,
                                                  container_name_copy_to=container_name_copy_to,
                                                  blob_name_copy_to=blob_name_copy_to,
                                                  source_copy_from=source_copy_from,
                                                  group_name_copy_to=group_name_copy_to)

        # Verify
        self.storage_service.parse_blob_url.assert_called_once_with(source_copy_from)
        self.storage_service._copy_blob.assert_called_once_with(group_name_copy_from=group_name_copy_from,
                                                                group_name_copy_to=group_name_copy_to,
                                                                storage_client=storage_client,
                                                                ulr_model_copy_from=blob_model_copy_from,
                                                                url_model_copy_to=blob_model_copy_to)
        self.assertEqual(blob_url, expected_blob_url)

    @mock.patch("cloudshell.cp.azure.domain.services.storage_service.BlobCopyOperationState")
    @mock.patch("cloudshell.cp.azure.domain.services.storage_service.AzureBlobUrlModel")
    def test_copy_blob_wait_until_copied_in_other_operation(self, blob_model_class, blob_copying_state):
        """Check that method will wait until image will be copied in another operation (thread)"""
        group_name_copy_from = "test_group_copy_from"
        group_name_copy_to = "test_group_copy_to"
        storage_name_copy_to = "test_storage_name_copy_to"
        container_name_copy_to = "test_container_name_copy_to"
        blob_name_copy_to = "test_blob_name_copy_to"
        source_copy_from = "https://teststoragesourse.blob.core.windows.net/testsourcecontainer/testsourceblob"
        storage_client = MagicMock()

        cache_key = (storage_name_copy_to, container_name_copy_to, blob_name_copy_to)
        self.storage_service._cached_copied_blob_urls = {
            cache_key: {
                "state": blob_copying_state.copying,
            }
        }

        class ExitLoopException(Exception):
            """Exception for existing infinite loop"""
            pass

        with mock.patch("cloudshell.cp.azure.domain.services.storage_service.time.sleep",
                        side_effect=ExitLoopException) as sleep:

            # Act
            with self.assertRaises(ExitLoopException):
                self.storage_service.copy_blob(storage_client=storage_client,
                                               group_name_copy_from=group_name_copy_from,
                                               storage_name_copy_to=storage_name_copy_to,
                                               container_name_copy_to=container_name_copy_to,
                                               blob_name_copy_to=blob_name_copy_to,
                                               source_copy_from=source_copy_from,
                                               group_name_copy_to=group_name_copy_to)

            sleep.assert_called_once()


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


class TestVMService(TestCase):
    def setUp(self):
        self.vm_service = VirtualMachineService()

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachine")
    def test__create_vm(self, virtual_machine_class):
        """Check that method will create VirtualMachine instance and execute create_or_update request"""
        compute_management_client = MagicMock()
        region = "test_region"
        group_name = "test_group_name"
        vm_name = "test_vm_name"
        hardware_profile = MagicMock()
        network_profile = MagicMock()
        os_profile = MagicMock()
        storage_profile = MagicMock()
        tags = MagicMock()
        vm = MagicMock()
        virtual_machine_class.return_value = vm

        # Act
        self.vm_service._create_vm(compute_management_client=compute_management_client,
                                   region=region,
                                   group_name=group_name,
                                   vm_name=vm_name,
                                   hardware_profile=hardware_profile,
                                   network_profile=network_profile,
                                   os_profile=os_profile,
                                   storage_profile=storage_profile,
                                   tags=tags)

        # Verify
        compute_management_client.virtual_machines.create_or_update.assert_called_with(group_name, vm_name, vm)
        virtual_machine_class.assert_called_once_with(hardware_profile=hardware_profile,
                                                      location=region,
                                                      network_profile=network_profile,
                                                      os_profile=os_profile,
                                                      storage_profile=storage_profile,
                                                      tags=tags)

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.StorageProfile")
    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.NetworkProfile")
    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.HardwareProfile")
    def test_create_vm(self, hardware_profile_class, network_profile_class, storage_profile_class):
        """Check that method will prepare all required parameters and call _create_vm method"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_vm_name"
        region = "test_region"
        tags = MagicMock()
        self.vm_service._create_vm = MagicMock()
        os_profile = MagicMock()
        hardware_profile = MagicMock()
        network_profile = MagicMock()
        storage_profile = MagicMock()
        self.vm_service._prepare_os_profile = MagicMock(return_value=os_profile)
        hardware_profile_class.return_value = hardware_profile
        network_profile_class.return_value = network_profile
        storage_profile_class.return_value = storage_profile

        # Act
        self.vm_service.create_vm(compute_management_client=compute_management_client,
                                  image_offer=MagicMock(),
                                  image_publisher=MagicMock(),
                                  image_sku=MagicMock(),
                                  image_version=MagicMock(),
                                  vm_credentials=MagicMock(),
                                  computer_name=MagicMock(),
                                  group_name=group_name,
                                  nic_id=MagicMock(),
                                  region=region,
                                  storage_name=MagicMock(),
                                  vm_name=vm_name,
                                  tags=tags,
                                  instance_type=MagicMock())

        # Verify
        self.vm_service._create_vm.assert_called_once_with(compute_management_client=compute_management_client,
                                                           group_name=group_name,
                                                           hardware_profile=hardware_profile,
                                                           network_profile=network_profile,
                                                           os_profile=os_profile,
                                                           region=region,
                                                           storage_profile=storage_profile,
                                                           tags=tags,
                                                           vm_name=vm_name)

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.StorageProfile")
    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.NetworkProfile")
    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.HardwareProfile")
    def test_create_vm_from_custom_image(self, hardware_profile_class, network_profile_class, storage_profile_class):
        """Check that method will prepare all required parameters and call _create_vm method"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_vm_name"
        region = "test_region"
        image_urn = "https://teststorage.blob.core.windows.net/testcontainer/testblob"
        tags = MagicMock()
        self.vm_service._create_vm = MagicMock()
        os_profile = MagicMock()
        hardware_profile = MagicMock()
        network_profile = MagicMock()
        storage_profile = MagicMock()
        self.vm_service._prepare_os_profile = MagicMock(return_value=os_profile)
        hardware_profile_class.return_value = hardware_profile
        network_profile_class.return_value = network_profile
        storage_profile_class.return_value = storage_profile

        # Act
        self.vm_service.create_vm_from_custom_image(compute_management_client=compute_management_client,
                                                    image_urn=image_urn,
                                                    image_os_type="Linux",
                                                    vm_credentials=MagicMock(),
                                                    computer_name=MagicMock(),
                                                    group_name=group_name,
                                                    nic_id=MagicMock(),
                                                    region=region,
                                                    storage_name=MagicMock(),
                                                    vm_name=vm_name,
                                                    tags=tags,
                                                    instance_type=MagicMock())

        # Verify
        self.vm_service._create_vm.assert_called_once_with(compute_management_client=compute_management_client,
                                                           group_name=group_name,
                                                           hardware_profile=hardware_profile,
                                                           network_profile=network_profile,
                                                           os_profile=os_profile,
                                                           region=region,
                                                           storage_profile=storage_profile,
                                                           tags=tags,
                                                           vm_name=vm_name)

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

    def test_get_active_vm(self):
        """Check that method will return Azure VM if instance exists and is in "Succeeded" provisioning state"""
        vm_name = "test_vm_name"
        group_name = "test_group_name"
        compute_client = mock.MagicMock()
        mocked_vm = mock.MagicMock(provisioning_state=self.vm_service.SUCCEEDED_PROVISIONING_STATE)
        self.vm_service.get_vm = mock.MagicMock(return_value=mocked_vm)

        # Act
        vm = self.vm_service.get_active_vm(compute_management_client=compute_client, group_name=group_name,
                                           vm_name=vm_name)

        # Verify
        self.assertIs(vm, mocked_vm)

    def test_get_active_vm_raises_exception(self):
        """Check that method will raise exception if VM is not in "Succeeded" provisioning state"""
        vm_name = "test_vm_name"
        group_name = "test_group_name"
        compute_client = mock.MagicMock()
        mocked_vm = mock.MagicMock(provisioning_state="SOME_PROVISION_STATE")
        self.vm_service.get_vm = mock.MagicMock(return_value=mocked_vm)

        with self.assertRaises(Exception):
            self.vm_service.get_active_vm(compute_management_client=compute_client, group_name=group_name,
                                          vm_name=vm_name)

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.OperatingSystemTypes")
    def test_prepare_image_os_type_returns_linux(self, operating_system_types):
        """Check that method will return Linux OS type"""
        image_os_type = "Linux"

        # Act
        res = self.vm_service._prepare_image_os_type(image_os_type=image_os_type)

        # Verify
        self.assertEqual(res, operating_system_types.linux)

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.OperatingSystemTypes")
    def test_prepare_image_os_type_returns_windows(self, operating_system_types):
        """Check that method will return Windows OS type"""
        image_os_type = "Windows"

        # Act
        res = self.vm_service._prepare_image_os_type(image_os_type=image_os_type)

        # Verify
        self.assertEqual(res, operating_system_types.windows)


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


class TestSecurityGroupService(TestCase):
    def setUp(self):
        self.network_service = MagicMock()
        self.security_group_service = SecurityGroupService(self.network_service)
        self.group_name = "test_group_name"
        self.security_group_name = "teststoragename"
        self.network_client = mock.MagicMock()

    def test_rule_priority_generator(self):
        """Check that method creates generator started from the given value plus increase step"""
        expected_values = [
            self.security_group_service.RULE_DEFAULT_PRIORITY,
            (self.security_group_service.RULE_DEFAULT_PRIORITY +
             self.security_group_service.RULE_PRIORITY_INCREASE_STEP),
            (self.security_group_service.RULE_DEFAULT_PRIORITY +
             self.security_group_service.RULE_PRIORITY_INCREASE_STEP * 2),
            (self.security_group_service.RULE_DEFAULT_PRIORITY +
             self.security_group_service.RULE_PRIORITY_INCREASE_STEP * 3)]

        # Act
        generator = self.security_group_service._rule_priority_generator([])

        # Verify
        generated_values = [next(generator) for _ in xrange(4)]
        self.assertEqual(expected_values, generated_values)

    def test_list_network_security_group(self):
        """Check that method calls azure network client to get list of NSGs and converts them into list"""
        # Act
        security_groups = self.security_group_service.list_network_security_group(
            network_client=self.network_client,
            group_name=self.group_name)

        # Verify
        self.network_client.network_security_groups.list.assert_called_once_with(self.group_name)
        self.assertIsInstance(security_groups, list)

    @mock.patch("cloudshell.cp.azure.domain.services.security_group.NetworkSecurityGroup")
    def test_create_network_security_group(self, nsg_class):
        """Check that method calls azure network client to create NSG and returns it result"""
        region = mock.MagicMock()
        tags = mock.MagicMock()
        nsg_class.return_value = nsg_model = mock.MagicMock()

        # Act
        nsg = self.security_group_service.create_network_security_group(
            network_client=self.network_client,
            group_name=self.group_name,
            security_group_name=self.security_group_name,
            region=region,
            tags=tags)

        # Verify
        self.network_client.network_security_groups.create_or_update.assert_called_once_with(
            resource_group_name=self.group_name,
            network_security_group_name=self.security_group_name,
            parameters=nsg_model)

        self.assertEqual(nsg, self.network_client.network_security_groups.create_or_update().result())

    @mock.patch("cloudshell.cp.azure.domain.services.security_group.SecurityRule")
    def test_prepare_security_group_rule(self, security_rule_class):
        """Check that method returns SecurityRule model"""
        security_rule_class.return_value = security_rule = mock.MagicMock()
        rule_data = mock.MagicMock()
        private_vm_ip = mock.MagicMock()
        priority = mock.MagicMock()

        # Act
        prepared_rule = self.security_group_service._prepare_security_group_rule(
            rule_data=rule_data,
            destination_addr=private_vm_ip,
            priority=priority)

        # Verify
        self.assertEqual(prepared_rule, security_rule)

    def test_create_network_security_group_rules_without_existing_rules(self):
        """Check that method will call network_client for NSG rules creation starting from default priority"""
        rule_data = mock.MagicMock()
        inbound_rules = [rule_data]
        private_vm_ip = mock.MagicMock()
        rule_model = mock.MagicMock()
        self.network_client.security_rules.list.return_value = []
        self.security_group_service._prepare_security_group_rule = mock.MagicMock(return_value=rule_model)

        # Act
        self.security_group_service.create_network_security_group_rules(
            network_client=self.network_client,
            group_name=self.group_name,
            security_group_name=self.security_group_name,
            inbound_rules=inbound_rules,
            destination_addr=private_vm_ip)

        # Verify
        self.security_group_service._prepare_security_group_rule.assert_called_once_with(
            priority=self.security_group_service.RULE_DEFAULT_PRIORITY,
            destination_addr=private_vm_ip,
            rule_data=rule_data)

        self.network_client.security_rules.create_or_update.assert_called_with(
            network_security_group_name=self.security_group_name,
            resource_group_name=self.group_name,
            security_rule_name=rule_model.name,
            security_rule_parameters=rule_model)

    def test_create_network_security_group_rules_with_existing_rules(self):
        """Check that method will call network_client for NSG rules creation starting from first available priority"""
        rule_data = mock.MagicMock()
        inbound_rules = [rule_data]
        private_vm_ip = mock.MagicMock()
        rule_model = mock.MagicMock()

        self.network_client.security_rules.list.return_value = [
            mock.MagicMock(priority=5000),
            mock.MagicMock(priority=100500),
            mock.MagicMock(priority=100000)]

        self.security_group_service._prepare_security_group_rule = mock.MagicMock(return_value=rule_model)

        # Act
        self.security_group_service.create_network_security_group_rules(
            network_client=self.network_client,
            group_name=self.group_name,
            security_group_name=self.security_group_name,
            inbound_rules=inbound_rules,
            destination_addr=private_vm_ip)

        # Verify
        self.security_group_service._prepare_security_group_rule.assert_called_once_with(
            priority=self.security_group_service.RULE_DEFAULT_PRIORITY,
            destination_addr=private_vm_ip,
            rule_data=rule_data)

        self.network_client.security_rules.create_or_update.assert_called_with(
            network_security_group_name=self.security_group_name,
            resource_group_name=self.group_name,
            security_rule_name=rule_model.name,
            security_rule_parameters=rule_model)

    def test_get_network_security_group(self):
        # Arrange
        self.network_security_group = MagicMock()
        self.security_group_service.list_network_security_group = MagicMock()
        self.security_group_service.list_network_security_group.return_value = self.network_security_group
        self.security_group_service._validate_network_security_group_is_single_per_group = MagicMock()

        # Act
        self.security_group_service.get_network_security_group(self.network_client, self.group_name)

        # Verify
        self.security_group_service.list_network_security_group.assert_called_once_with(
            network_client=self.network_client,
            group_name=self.group_name)
        self.security_group_service._validate_network_security_group_is_single_per_group.assert_called_once_with(
            self.network_security_group,
            self.group_name)

    def test_delete_security_rules(self):
        # Arrange
        self.network_security_group = MagicMock()
        network_client = MagicMock()
        private_ip_address = Mock()
        resource_group_name = "group_name"
        vm_name = "vm_name"
        security_group = NetworkSecurityGroup()
        security_group.name = "security_group_name"
        security_rule = Mock()
        security_rule.name = "rule_name"
        security_rule.destination_address_prefix = private_ip_address
        security_rules = [security_rule]
        security_group.security_rules = security_rules
        self.security_group_service.get_network_security_group = MagicMock()
        self.security_group_service.get_network_security_group.return_value = security_group
        self.network_service.get_private_ip = Mock(return_value=private_ip_address)

        # Act
        self.security_group_service.delete_security_rules(network_client, resource_group_name, vm_name)

        # Verify
        network_client.security_rules.delete.assert_called_once_with(
            resource_group_name=resource_group_name,
            network_security_group_name=security_group.name,
            security_rule_name=security_rule.name
        )
