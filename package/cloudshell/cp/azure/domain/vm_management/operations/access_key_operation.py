from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.key_pair import KeyPairService


class AccessKeyOperation(object):
    def __init__(self, key_pair_service, storage_service):
        """
        :param KeyPairService key_pair_service:
        :param StorageService storage_service:
        :return:
        """
        self.key_pair_service = key_pair_service
        self.storage_service = storage_service

    def get_access_key(self, storage_client, group_name):
        """
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param group_name: (str) the name of the resource group on Azure
        :return:
        """
        storage_account_name = self.storage_service.get_sandbox_storage_account_name(storage_client=storage_client,
                                                                                     group_name=group_name)

        # cloudshell.cp.azure.models.ssh_key.SSHKey instance
        ssh_key = self.key_pair_service.get_key_pair(storage_client=storage_client,
                                                     group_name=group_name,
                                                     storage_name=storage_account_name)

        return ssh_key.private_key
