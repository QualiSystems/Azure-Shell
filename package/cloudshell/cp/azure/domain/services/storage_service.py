from threading import Lock

import azure
from azure.mgmt.storage.models import SkuName, StorageAccountCreateParameters
from azure.storage.file import FileService


class StorageService(object):
    def __init__(self):
        self._lock = Lock()
        self._cached_file_services = {}

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
        account_keys = storage_client.storage_accounts.list_keys(group_name, storage_name)
        account_key = account_keys.keys[0]

        return account_key.value

    def _get_file_service(self, storage_client, group_name, storage_name):
        """Get Azure file service for given storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return: azure.storage.file.FileService instance
        """
        cached_key = (group_name, storage_name)

        with self._lock:
            try:
                file_service = self._cached_file_services[cached_key]
            except KeyError:
                account_key = self._get_storage_account_key(
                    storage_client=storage_client,
                    group_name=group_name,
                    storage_name=storage_name)

                file_service = FileService(account_name=storage_name, account_key=account_key)
                self._cached_file_services[cached_key] = file_service

        return file_service

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
