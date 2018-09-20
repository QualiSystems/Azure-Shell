from datetime import datetime
from datetime import timedelta
from threading import Lock
import time
from urlparse import urlparse

import azure
from azure.mgmt.storage.models import SkuName, StorageAccountCreateParameters
from azure.storage.file import FileService
from azure.storage.blob import BlockBlobService
from azure.storage.blob.models import BlobPermissions
from retrying import retry

from cloudshell.cp.azure.common.exceptions.validation_error import ValidationError
from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error
from cloudshell.cp.azure.models.azure_blob_url import AzureBlobUrlModel
from cloudshell.cp.azure.models.blob_copy_operation import BlobCopyOperationState
from cloudshell.cp.azure.common.exceptions.cancellation_exception import CancellationException


class StorageService(object):
    SAS_TOKEN_EXPIRATION_DAYS = 365

    def __init__(self, cancellation_service):
        """

        :param cancellation_service: cloudshell.cp.azure.domain.services.command_cancellation.CommandCancellationService
        """
        self.cancellation_service = cancellation_service
        self._account_keys_lock = Lock()
        self._file_services_lock = Lock()
        self._blob_services_lock = Lock()
        self._copied_blob_urls_lock = Lock()
        self._cached_account_keys = {}
        self._cached_file_services = {}
        self._cached_blob_services = {}
        self._cached_copied_blob_urls = {}

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_storage_account(self, storage_client, group_name, region, storage_account_name, tags,
                               wait_until_created=False):
        """

        :param storage_client:
        :param group_name:
        :param region:
        :param storage_account_name:
        :param tags:
        :return:
        """

        kind_storage_value = azure.mgmt.storage.models.Kind.storage
        sku_name = SkuName.standard_lrs
        sku = azure.mgmt.storage.models.Sku(sku_name)
        storage_accounts_create = storage_client.storage_accounts.create(group_name,
                                                                         storage_account_name,
                                                                         StorageAccountCreateParameters(
                                                                                 sku=sku,
                                                                                 kind=kind_storage_value,
                                                                                 location=region,
                                                                                 tags=tags),
                                                                         raw=False)
        if wait_until_created:
            storage_accounts_create.wait()

        return storage_account_name

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_storage_per_resource_group(self, storage_client, group_name):
        """

        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param group_name:
        :return:
        """
        return list(storage_client.storage_accounts.list_by_resource_group(group_name))

    # changed the retry max attempt number to 20, because when deploying multiple sandboxes, would get an error that
    # resource group had not been created quite consistently. This is not a magic number, its just found
    # to be effective with 8~ concurrent sandbox launches. Might be changed in the future
    @retry(stop_max_attempt_number=20, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def _get_storage_account_key(self, storage_client, group_name, storage_name):
        """Get firsts storage account access key for some storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return: (str) storage access key
        """
        cached_key = (group_name, storage_name)
        account_key = self._cached_account_keys.get(cached_key)

        if account_key is None:
            with self._account_keys_lock:
                account_key = self._cached_account_keys.get(cached_key)
                if account_key is None:
                    account_keys = storage_client.storage_accounts.list_keys(group_name, storage_name)
                    account_key = account_keys.keys[0]
                    account_key = account_key.value
                    self._cached_account_keys[cached_key] = account_key

        return account_key

    def _get_file_service(self, storage_client, group_name, storage_name):
        """Get Azure file service for given storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return: azure.storage.file.FileService instance
        """
        cached_key = (group_name, storage_name)
        file_service = self._cached_file_services.get(cached_key)

        if file_service is None:
            with self._file_services_lock:
                file_service = self._cached_file_services.get(cached_key)
                if file_service is None:
                    account_key = self._get_storage_account_key(
                            storage_client=storage_client,
                            group_name=group_name,
                            storage_name=storage_name)

                    file_service = FileService(account_name=storage_name, account_key=account_key)
                    self._cached_file_services[cached_key] = file_service

        return file_service

    def _get_blob_service(self, storage_client, group_name, storage_name):
        """Get Azure Blob service for given storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return: azure.storage.blob.BlockBlobService instance
        """
        cached_key = (group_name, storage_name)
        blob_service = self._cached_blob_services.get(cached_key)

        if blob_service is None:
            with self._blob_services_lock:
                blob_service = self._cached_blob_services.get(cached_key)
                if blob_service is None:
                    account_key = self._get_storage_account_key(
                            storage_client=storage_client,
                            group_name=group_name,
                            storage_name=storage_name)

                    blob_service = BlockBlobService(account_name=storage_name, account_key=account_key)
                    self._cached_blob_services[cached_key] = blob_service

        return blob_service

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_file(self, storage_client, group_name, storage_name, share_name, directory_name, file_name):
        """Read file from the Azure storage as a sting

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :param share_name: (str) share file name on Azure
        :param directory_name: (str) directory name for share file name on Azure
        :param file_name: (str) file name within directory
        :return: azure.storage.file.models.File instance
        """
        file_service = self._get_file_service(
                storage_client=storage_client,
                group_name=group_name,
                storage_name=storage_name)

        azure_file = file_service.get_file_to_bytes(
                share_name=share_name,
                directory_name=directory_name,
                file_name=file_name)

        return azure_file

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_file(self, storage_client, group_name, storage_name, share_name,
                    directory_name, file_name, file_content):
        """Create file on the Azure

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :param share_name: (str) share file name on Azure
        :param directory_name: (str) directory name for share file name on Azure
        :param file_name: (str) file name within directory
        :param file_content: (str) file content to be saved
        :return:
        """
        file_service = self._get_file_service(
                storage_client=storage_client,
                group_name=group_name,
                storage_name=storage_name)

        file_service.create_share(share_name=share_name, fail_on_exist=False)
        file_service.create_file_from_bytes(share_name=share_name,
                                            directory_name=directory_name,
                                            file_name=file_name,
                                            file=file_content)

    def parse_blob_url(self, blob_url):
        """Parses Blob URL into AzureBlobUrlModel

        :param blob_url: (str) Azure Blob URL ("https://someaccount.blob.core.windows.net/container/blobname")
        :return: cloudshell.cp.azure.models.azure_blob_url.AzureBlobUrlModel instance
        """
        parsed_blob_url = urlparse(blob_url)
        splitted_path = parsed_blob_url.path.split('/')
        blob_name = splitted_path[-1]
        container_name = splitted_path[-2]
        storage_name = parsed_blob_url.netloc.split('.', 1)[0]

        return AzureBlobUrlModel(storage_name=storage_name,
                                 container_name=container_name,
                                 blob_name=blob_name)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def _wait_until_blob_copied(self, blob_service, container_name, blob_name, cancellation_context,
                                logger, sleep_time=10):
        """Wait until Blob file is copied from one storage to another

        :param blob_service: azure.storage.blob.BlockBlobService instance
        :param container_name: (str) container name where Blob was copied
        :param blob_name: (str) Blob name where Blob was copied
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :param logger: logging.Logger instance
        :param sleep_time: (int) seconds to wait before check requests
        :return:
        """
        while True:
            blob = blob_service.get_blob_properties(container_name, blob_name)

            try:
                self.cancellation_service.check_if_cancelled(cancellation_context)
            except CancellationException:
                blob_service.abort_copy_blob(container_name, blob_name, blob.properties.copy.id)
                raise

            if blob.properties.copy.status == "success":
                logger.info("Image was successfully copied to {}/{}".format(container_name, blob_name))
                break

            elif blob.properties.copy.status in ["aborted", "failed"]:
                blob_url = blob_service.make_blob_url(container_name, blob_name)
                logger.error("Image was not copied to {}/{}. Status: {}".format(
                        container_name, blob_name, blob.properties.copy.status))

                raise Exception("Copying of file {} failed".format(blob_url))

            logger.info("Image is still copying to {}/{}. Operation status: is '{}'"
                        .format(container_name, blob_name, blob.properties.copy.status))

            time.sleep(sleep_time)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def _copy_blob(self, storage_client, group_name_copy_from, group_name_copy_to,
                   ulr_model_copy_from, url_model_copy_to, cancellation_context, logger):
        """Copy Blob from one storage account to another

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name_copy_from: (str) resource group of the copied Blob
        :param group_name_copy_to: (str) resource group where Blob will be copied
        :param ulr_model_copy_from: cloudshell.cp.azure.models.azure_blob_url.AzureBlobUrlModel instance copy from
        :param url_model_copy_to: cloudshell.cp.azure.models.azure_blob_url.AzureBlobUrlModel instance copy to
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :param logger: logging.Logger instance
        :return: copied image URL (str) Azure Blob URL
        """
        logger.info("Get Blob Service for storage {} under RG {}".format(ulr_model_copy_from.storage_name,
                                                                         group_name_copy_from))

        blob_service_copy_from = self._get_blob_service(
                storage_client=storage_client,
                group_name=group_name_copy_from,
                storage_name=ulr_model_copy_from.storage_name)

        expiration_date = datetime.now() + timedelta(days=self.SAS_TOKEN_EXPIRATION_DAYS)

        logger.info("Generate SAS token for the blob {}/{}".format(ulr_model_copy_from.container_name,
                                                                   ulr_model_copy_from.blob_name))

        sas_token = blob_service_copy_from.generate_blob_shared_access_signature(
                container_name=ulr_model_copy_from.container_name,
                blob_name=ulr_model_copy_from.blob_name,
                permission=BlobPermissions.READ,
                expiry=expiration_date)

        copy_source = blob_service_copy_from.make_blob_url(container_name=ulr_model_copy_from.container_name,
                                                           blob_name=ulr_model_copy_from.blob_name,
                                                           sas_token=sas_token)

        logger.info("Get Blob Service for storage {} under RG {}".format(url_model_copy_to.storage_name,
                                                                         group_name_copy_to))

        blob_service_copy_to = self._get_blob_service(
                storage_client=storage_client,
                group_name=group_name_copy_to,
                storage_name=url_model_copy_to.storage_name)

        if not blob_service_copy_to.exists(container_name=url_model_copy_to.container_name,
                                           blob_name=url_model_copy_to.blob_name):
            logger.info("Blob {}/{} doesn't exist, start copying".format(url_model_copy_to.container_name,
                                                                         url_model_copy_to.blob_name))

            logger.info("Create Blob container {}".format(url_model_copy_to.container_name))
            blob_service_copy_to.create_container(container_name=url_model_copy_to.container_name, fail_on_exist=False)

            logger.info("Start async copy blob operation on Azure for {}".format(copy_source))
            blob_service_copy_to.copy_blob(container_name=url_model_copy_to.container_name,
                                           blob_name=url_model_copy_to.blob_name,
                                           copy_source=copy_source)

            self._wait_until_blob_copied(blob_service=blob_service_copy_to,
                                         container_name=url_model_copy_to.container_name,
                                         blob_name=url_model_copy_to.blob_name,
                                         cancellation_context=cancellation_context,
                                         logger=logger)

        return blob_service_copy_to.make_blob_url(url_model_copy_to.container_name, url_model_copy_to.blob_name)

    def copy_blob(self, storage_client, group_name_copy_to, storage_name_copy_to, container_name_copy_to,
                  blob_name_copy_to, source_copy_from, group_name_copy_from, cancellation_context, logger):
        """Copy Blob from the given source_copy_from URL

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name_copy_to: (str) resource group where Blob will be copied
        :param storage_name_copy_to: (str) storage account where Blob will be copied
        :param container_name_copy_to: (str) storage container where Blob will be copied
        :param blob_name_copy_to: (str) name for copied Blob file
        :param source_copy_from: (str) Azure Blob URL ("https://someaccount.blob.core.windows.net/container/blobname")
        :param group_name_copy_from: (str) resource group of the copied Blob
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :param logging.Logger logger:
        :return: copied image URL (str) Azure Blob URL
        """
        ulr_model_copy_from = self.parse_blob_url(source_copy_from)
        copied_blob_key = (storage_name_copy_to, container_name_copy_to, blob_name_copy_to)

        if not (copied_blob_key in self._cached_copied_blob_urls
                and self._cached_copied_blob_urls[copied_blob_key]["state"] is BlobCopyOperationState.success):

            need_to_copy = False  # image isn't uploaded by other thread
            need_to_wait = False  # image is uploading by other thread right now

            with self._copied_blob_urls_lock:
                copied_blob = self._cached_copied_blob_urls.get(copied_blob_key)

                if copied_blob is None or copied_blob["state"] is BlobCopyOperationState.failed:
                    self._cached_copied_blob_urls[copied_blob_key] = {
                        "state": BlobCopyOperationState.copying,
                        "result": None
                    }
                    need_to_copy = True
                    logger.info("Image {} is not in cache/copying state. Need to start copying ".format(
                            source_copy_from))

                elif copied_blob["state"] is BlobCopyOperationState.copying:
                    logger.info("Image {} is copying in other operation. Will wait for the result".format(
                            source_copy_from))

                    need_to_wait = True

            if need_to_wait:
                while True:
                    self.cancellation_service.check_if_cancelled(cancellation_context)
                    copied_blob_state = self._cached_copied_blob_urls[copied_blob_key]["state"]

                    if copied_blob_state is BlobCopyOperationState.success:
                        logger.info("Image {} copying was successfully completed in another operation".format(
                                source_copy_from))
                        break

                    elif copied_blob_state is BlobCopyOperationState.failed:
                        logger.error("Image {} copying was failed in another operation".format(
                                source_copy_from))
                        raise Exception("Blob copying was failed")

                    logger.info("Image {} is copying in other operation. Wait for the result...".format(
                            source_copy_from))

                    time.sleep(1)

            elif need_to_copy:
                logger.info("Start copying image {}".format(source_copy_from))
                url_model_copy_to = AzureBlobUrlModel(storage_name=storage_name_copy_to,
                                                      container_name=container_name_copy_to,
                                                      blob_name=blob_name_copy_to)
                try:
                    copied_blob_url = self._copy_blob(storage_client=storage_client,
                                                      group_name_copy_from=group_name_copy_from,
                                                      group_name_copy_to=group_name_copy_to,
                                                      ulr_model_copy_from=ulr_model_copy_from,
                                                      url_model_copy_to=url_model_copy_to,
                                                      cancellation_context=cancellation_context,
                                                      logger=logger)
                except Exception:
                    with self._copied_blob_urls_lock:
                        self._cached_copied_blob_urls[copied_blob_key]["state"] = BlobCopyOperationState.failed

                    logger.exception("Image {} copying was failed".format(source_copy_from))
                    raise

                logger.info("Image {} was successfully copied to {}".format(source_copy_from, copied_blob_url))

                with self._copied_blob_urls_lock:
                    self._cached_copied_blob_urls[copied_blob_key]["state"] = BlobCopyOperationState.success
                    self._cached_copied_blob_urls[copied_blob_key]["result"] = copied_blob_url

        copied_image_url = self._cached_copied_blob_urls[copied_blob_key]["result"]
        logger.info("Copyied Image URL: {}".format(copied_image_url))

        return copied_image_url

    def delete_blob(self, storage_client, group_name, storage_name, container_name, blob_name):
        """Delete Blob file from the Azure

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :param container_name: (str) the name of the container on Azure
        :param blob_name: (ste) the name of the Blob file
        :return:
        """
        blob_service = self._get_blob_service(storage_client=storage_client,
                                              group_name=group_name,
                                              storage_name=storage_name)

        blob_service.delete_blob(container_name=container_name, blob_name=blob_name)

    def validate_single_storage_account(self, storage_accounts_list):
        """
        Validates that there is only 1 storage account in the provided list
        :param storage_accounts_list:
        :return:
        """
        if not len(storage_accounts_list) == 1:
            raise ValidationError(
                    "Sandbox Resource Group should contain only one storage account but found {} storage accounts"
                    .format(len(storage_accounts_list)))

    def get_sandbox_storage_account_name(self, storage_client, group_name):
        """
        Get storage account name for given reservation

        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param str group_name:
        :return: storage account name
        :rtype: str
        """
        storage_accounts_list = self.get_storage_per_resource_group(storage_client, group_name)
        self.validate_single_storage_account(storage_accounts_list)
        return storage_accounts_list[0].name
