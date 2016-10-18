import azure
from azure.mgmt.storage.models import SkuName, StorageAccountCreateParameters


class StorageService(object):
    def __init__(self):
        pass

    def create_storage_account(self, storage_client, group_name, region, storage_account_name, tags):
        """

        :param storage_client:
        :param group_name:
        :param region:
        :param storage_account_name:
        :param tags:
        :return:
        """

        kind_storage_value = azure.mgmt.storage.models.Kind.storage.value
        sku_name = SkuName.standard_lrs
        sku = azure.mgmt.storage.models.Sku(sku_name)
        # storage_accounts_create = storage_client.storage_accounts.create(group_name,
        #                                                                  storage_account_name,
        #                                                                  StorageAccountCreateParameters(
        #                                                                      sku=sku,
        #                                                                      kind=kind_storage_value,
        #                                                                      location=region,
        #                                                                      tags=tags))
        # storage_accounts_create.wait()  # async operation

        storage_client.storage_accounts.create(group_name,
                                               storage_account_name,
                                               StorageAccountCreateParameters(
                                                   sku=sku,
                                                   kind=kind_storage_value,
                                                   location=region,
                                                   tags=tags),
                                               raw=True)
        return storage_account_name

    def get_storage_per_resource_group(self, storage_client, group_name):
        """

        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param group_name:
        :return:
        """
        return list(storage_client.storage_accounts.list_by_resource_group(group_name))

