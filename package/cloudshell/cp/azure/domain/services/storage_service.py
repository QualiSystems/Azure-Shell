import azure
from azure.mgmt.storage.models import SkuName, StorageAccountCreateParameters


class StorageService(object):
    def create_storage_account(self, storage_client, group_name, region, storage_account_name, tags):
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
        storage_accounts_create = storage_client.storage_accounts.create(group_name, storage_account_name,
                                                                         StorageAccountCreateParameters(
                                                                             sku=sku,
                                                                             kind=kind_storage_value,
                                                                             location=region,
                                                                             tags=tags),
                                                                         raw=False)
        #storage_accounts_create.wait()  # async operation
    def get_storage_account_key(self, storage_client, group_name, storage_name):
        """Get firsts storage account access key for some storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return: (str) storage access key
        """
        account_keys = storage_client.storage_accounts.list_keys(group_name, storage_name)
        account_key = account_keys.keys[0]

        return account_key.value
