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


class StorageService(object):
    SAS_TOKEN_EXPIRATION_DAYS = 365

    def __init__(self):
        self._account_keys_lock = Lock()
        self._file_services_lock = Lock()
        self._blob_services_lock = Lock()
        self._cached_account_keys = {}
        self._cached_file_services = {}
        self._cached_blob_services = {}

    def create_storage_account(self, storage_client, group_name, region, storage_account_name, tags,wait_until_created=False):
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

    def get_storage_per_resource_group(self, storage_client, group_name):
        """

        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param group_name:
        :return:
        """
        return list(storage_client.storage_accounts.list_by_resource_group(group_name))

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
        """Parses Blob URL into Azure parameters

        :param blob_url: (str) Azure Blob URL ("https://someaccount.blob.core.windows.net/container/blobname")
        :return: tuple(storage_name, container_name, blob_name)
        """
        parsed_blob_url = urlparse(blob_url)
        splitted_path = parsed_blob_url.path.split('/')
        blob_name = splitted_path[-1]
        container_name = splitted_path[-2]
        storage_name = parsed_blob_url.netloc.split('.', 1)[0]

        return storage_name, container_name, blob_name

    def _wait_until_blob_copied(self, blob_service, container_name, blob_name, sleep_time=10):
        """Wait until Blob file is copied from one storage to another

        :param blob_service: azure.storage.blob.BlockBlobService instance
        :param container_name: (str) container name where Blob was copied
        :param blob_name: (str) Blob name where Blob was copied
        :param sleep_time: (int) seconds to wait before check requests
        :return:
        """
        while True:
            blob = blob_service.get_blob_properties(container_name, blob_name)

            if blob.properties.copy.status == "success":
                return

            elif blob.properties.copy.status in ["aborted", "failed"]:
                blob_url = blob_service.make_blob_url(container_name, blob_name)
                raise Exception("Copying of file {} failed".format(blob_url))

            time.sleep(sleep_time)

    def copy_blob(self, storage_client, group_name_copy_to, storage_name_copy_to, container_name_copy_to,
                  blob_name_copy_to, source_copy_from, group_name_copy_from):
        """Copy Blob from the given source_copy_from URL

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name_copy_to: (str) resource group where Blob will be copied
        :param storage_name_copy_to: (str) storage account where Blob will be copied
        :param container_name_copy_to: (str) storage container where Blob will be copied
        :param blob_name_copy_to: (str) name for copied Blob file
        :param source_copy_from: (str) Azure Blob URL ("https://someaccount.blob.core.windows.net/container/blobname")
        :param group_name_copy_from: (str) resource group of the copied Blob
        :return: copied image URL (str) Azure Blob URL
        """
        storage_name_copy_from, container_name_copy_from, blob_name_copy_from = self.parse_blob_url(source_copy_from)

        blob_service_copy_from = self._get_blob_service(
            storage_client=storage_client,
            group_name=group_name_copy_from,
            storage_name=storage_name_copy_from)

        expiration_date = datetime.now() + timedelta(days=self.SAS_TOKEN_EXPIRATION_DAYS)

        sas_token = blob_service_copy_from.generate_blob_shared_access_signature(
            container_name=container_name_copy_from,
            blob_name=blob_name_copy_from,
            permission=BlobPermissions.READ,
            expiry=expiration_date)

        copy_source = blob_service_copy_from.make_blob_url(container_name=container_name_copy_from,
                                                           blob_name=blob_name_copy_from,
                                                           sas_token=sas_token)

        blob_service_copy_to = self._get_blob_service(
            storage_client=storage_client,
            group_name=group_name_copy_to,
            storage_name=storage_name_copy_to)

        if not blob_service_copy_to.exists(container_name=container_name_copy_to, blob_name=blob_name_copy_to):
            blob_service_copy_to.create_container(container_name=container_name_copy_to, fail_on_exist=False)
            blob_service_copy_to.copy_blob(container_name=container_name_copy_to,
                                           blob_name=blob_name_copy_to,
                                           copy_source=copy_source)

            self._wait_until_blob_copied(blob_service=blob_service_copy_to,
                                         container_name=container_name_copy_to,
                                         blob_name=blob_name_copy_to)

        return blob_service_copy_to.make_blob_url(container_name_copy_to, blob_name_copy_to)
