from unittest import TestCase

import mock
from mock import MagicMock, Mock


from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.common.exceptions.cancellation_exception import CancellationException
from tests.helpers.test_helper import TestHelper


class TestStorageService(TestCase):
    def setUp(self):
        self.cancellation_service = MagicMock()
        self.storage_service = StorageService(cancellation_service=self.cancellation_service)
        self.group_name = "test_group_name"
        self.storage_name = "teststoragename"
        self.storage_client = mock.MagicMock()
        self.logger = mock.MagicMock()

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

        with mock.patch("cloudshell.cp.azure.domain.services.storage_service.StorageAccountCreateParameters") as stcp:
            self.storage_service.create_storage_account(storage_client, group_name, region, account_name, tags)

            # Verify
            storage_client.storage_accounts.create.assert_called_with(group_name, account_name,
                                                                      stcp(
                                                                          sku=MagicMock(),
                                                                          kind=kind_storage_value,
                                                                          location=region,
                                                                          tags=tags),
                                                                      raw=False)

    def test_create_storage_account_wait_for_result(self):
        # Arrange
        storage_accounts_create = Mock(return_value=mock.MagicMock())
        storage_accounts_create.wait = MagicMock()
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
        cancellation_context = MagicMock()
        blob.properties.copy.status = "success"
        blob_service.get_blob_properties.return_value = blob

        # Act
        self.storage_service._wait_until_blob_copied(
            blob_service=blob_service,
            container_name=container_name,
            blob_name=blob_name,
            cancellation_context=cancellation_context,
            logger=self.logger)

        # Verify
        blob_service.get_blob_properties.assert_called_once_with(container_name, blob_name)

    def test_wait_until_blob_copied_ends_with_failed_status(self):
        """Check that method will raise Exception if Blob copy operation ended with the failed status"""
        container_name = "testcontainer"
        blob_name = "testblobname"
        blob_service = MagicMock()
        blob = MagicMock()
        cancellation_context = MagicMock()
        blob.properties.copy.status = "failed"
        blob_service.get_blob_properties.return_value = blob

        with self.assertRaises(Exception):
            self.storage_service._wait_until_blob_copied(
                blob_service=blob_service,
                container_name=container_name,
                blob_name=blob_name,
                cancellation_context=cancellation_context,
                logger=self.logger)

    def test_wait_until_blob_copied_command_was_cancelled(self):
        """Check that method will abort copying and re-raise CancellationException if command will be cancelled"""
        container_name = "testcontainer"
        blob_name = "testblobname"
        blob_service = MagicMock()
        blob = MagicMock()
        cancellation_context = MagicMock()
        blob.properties.copy.status = "failed"
        blob_service.get_blob_properties.return_value = blob
        self.storage_service.cancellation_service = MagicMock()
        self.storage_service.cancellation_service.check_if_cancelled.side_effect = CancellationException

        with self.assertRaises(CancellationException):
            self.storage_service._wait_until_blob_copied(
                blob_service=blob_service,
                container_name=container_name,
                blob_name=blob_name,
                cancellation_context=cancellation_context,
                logger=self.logger)

    def test_wait_until_blob_copied_will_wait_for_operation(self):
        """Check that method will continue loop if Blob copy operation is in copying status"""
        container_name = "testcontainer"
        blob_name = "testblobname"
        blob_service = MagicMock()
        blob = MagicMock()
        cancellation_context = MagicMock(is_cancelled=False)
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
                    logger=self.logger,
                    cancellation_context=cancellation_context,
                    sleep_time=sleep_time)

            # Verify
            sleep.assert_called_once_with(sleep_time)

    def test__copy_blob_file_already_exists(self):
        """Check that method will not copy Blob if such one already exists under the storage/container"""
        group_name_copy_from = "testgroupcopyfrom"
        group_name_copy_to = "testgroupcopyto"
        storage_client = MagicMock()
        cancellation_context = MagicMock()
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
                                                   url_model_copy_to=url_model_copy_to,
                                                   cancellation_context=cancellation_context,
                                                   logger=self.logger)

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
        cancellation_context = MagicMock()
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
                                                   url_model_copy_to=url_model_copy_to,
                                                   cancellation_context=cancellation_context,
                                                   logger=self.logger)

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
            blob_service=blob_service,
            cancellation_context=cancellation_context,
            logger=self.logger)

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
        cancellation_context = MagicMock()
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
                                                  group_name_copy_to=group_name_copy_to,
                                                  cancellation_context=cancellation_context,
                                                  logger=self.logger)

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
        cancellation_context = MagicMock()
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
                                                  group_name_copy_to=group_name_copy_to,
                                                  cancellation_context=cancellation_context,
                                                  logger=self.logger)

        # Verify
        self.storage_service.parse_blob_url.assert_called_once_with(source_copy_from)
        self.storage_service._copy_blob.assert_called_once_with(group_name_copy_from=group_name_copy_from,
                                                                group_name_copy_to=group_name_copy_to,
                                                                storage_client=storage_client,
                                                                ulr_model_copy_from=blob_model_copy_from,
                                                                url_model_copy_to=blob_model_copy_to,
                                                                cancellation_context=cancellation_context,
                                                                logger=self.logger)
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
        cancellation_context = MagicMock()

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
                                               group_name_copy_to=group_name_copy_to,
                                               cancellation_context=cancellation_context,
                                               logger=self.logger)

            sleep.assert_called_once()

    def test_delete_blob(self):
        """Check that method will call delete_blob method on the blob service"""
        blob_service = MagicMock()
        container_name = "test_container_name"
        blob_name = "test_blob_name"
        self.storage_service._get_blob_service = MagicMock(return_value=blob_service)

        # Act
        self.storage_service.delete_blob(storage_client=self.storage_client,
                                         group_name=self.group_name,
                                         storage_name=self.storage_name,
                                         container_name=container_name,
                                         blob_name=blob_name)

        # Verify
        self.storage_service._get_blob_service.assert_called_once_with(storage_client=self.storage_client,
                                                                       group_name=self.group_name,
                                                                       storage_name=self.storage_name)

        blob_service.delete_blob.assert_called_once_with(container_name=container_name, blob_name=blob_name)

    def test_get_sandbox_storage_account_name(self):
        storage_client = MagicMock()
        group_name = "testgroupname"
        sandbox_storage_account_name = "teststorageaccountname"
        storage_account = MagicMock()
        storage_account.name = sandbox_storage_account_name
        self.storage_service.get_storage_per_resource_group = MagicMock(return_value=[storage_account])

        # Act
        storage_account_name = self.storage_service.get_sandbox_storage_account_name(
            storage_client=storage_client,
            group_name=group_name)

        # Verify
        self.storage_service.get_storage_per_resource_group.assert_called_once_with(storage_client, group_name)
        self.assertEqual(storage_account_name, sandbox_storage_account_name)

