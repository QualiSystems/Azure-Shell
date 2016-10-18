import azure
from azure.mgmt.storage.models import SkuName, StorageAccountCreateParameters
from azure.storage.file import FileService

from cloudshell.cp.azure.models.ssh_key import SSHKey


class StorageService(object):
    FILE_SHARE_NAME = "sshkeypair"
    FILE_SHARE_DIRECTORY = ""
    SSH_PUB_KEY_NAME = "id_rsa.pub"
    SSH_PRIVATE_KEY_NAME = "id_rsa"

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
        storage_accounts_create = storage_client.storage_accounts.create(group_name, storage_account_name,
                                                                         StorageAccountCreateParameters(
                                                                             sku=sku,
                                                                             kind=kind_storage_value,
                                                                             location=region,
                                                                             tags=tags))
        storage_accounts_create.wait()  # async operation

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

    def save_key_pair(self, storage_client, key_pair, group_name, storage_name):
        """Save SSH key pair to the Azure storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param key_pair: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return:
        """
        account_key = self._get_storage_account_key(storage_client, group_name, storage_name)

        file_service = FileService(account_name=storage_name,
                                   account_key=account_key)

        file_service.create_share(self.FILE_SHARE_NAME)

        file_service.create_file_from_bytes(share_name=self.FILE_SHARE_NAME,
                                            directory_name=self.FILE_SHARE_DIRECTORY,
                                            file_name=self.SSH_PUB_KEY_NAME,
                                            file=key_pair.public_key)

        file_service.create_file_from_bytes(share_name=self.FILE_SHARE_NAME,
                                            directory_name=self.FILE_SHARE_DIRECTORY,
                                            file_name=self.SSH_PRIVATE_KEY_NAME,
                                            file=key_pair.private_key)

    def get_key_pair(self, storage_client, group_name, storage_name):
        """Get SSH key pair from the Azure storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        """
        account_key = self._get_storage_account_key(storage_client, group_name, storage_name)

        file_service = FileService(account_name=storage_name,
                                   account_key=account_key)

        pub_key_file = file_service.get_file_to_bytes(
            share_name=self.FILE_SHARE_NAME,
            directory_name=self.FILE_SHARE_DIRECTORY,
            file_name=self.SSH_PUB_KEY_NAME)

        private_key_file = file_service.get_file_to_bytes(
            share_name=self.FILE_SHARE_NAME,
            directory_name=self.FILE_SHARE_DIRECTORY,
            file_name=self.SSH_PRIVATE_KEY_NAME)

        return SSHKey(private_key=private_key_file.content,
                      public_key=pub_key_file.content)
