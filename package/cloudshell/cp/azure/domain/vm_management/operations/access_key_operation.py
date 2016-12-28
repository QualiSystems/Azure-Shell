from azure.mgmt.storage.models import StorageAccount
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.key_pair import KeyPairService
from cloudshell.cp.azure.common.validtors.provider import ValidatorProvider


class AccessKeyOperation(object):
    def __init__(self, key_pair_service, storage_service, validator_provider):
        """
        :param KeyPairService key_pair_service:
        :param StorageService storage_service:
        :param ValidatorProvider validator_provider:
        :return:
        """
        self.key_pair_service = key_pair_service
        self.storage_service = storage_service
        self.validator_provider = validator_provider

    def get_access_key(self, storage_client, group_name):
        """
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param group_name: (str) the name of the resource group on Azure
        :return:
        """
        storage_accounts_list = self.storage_service.get_storage_per_resource_group(
                storage_client,
                group_name)

        self.validator_provider.try_validate(resource_type=StorageAccount, resource=storage_accounts_list)
        storage_account_name = storage_accounts_list[0].name

        # cloudshell.cp.azure.models.ssh_key.SSHKey instance
        ssh_key = self.key_pair_service.get_key_pair(storage_client=storage_client,
                                                     group_name=group_name,
                                                     storage_name=storage_account_name)

        return ssh_key.private_key
