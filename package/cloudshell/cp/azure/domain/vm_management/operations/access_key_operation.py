from retrying import retry
from azure.mgmt.storage.models import StorageAccount

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error
from cloudshell.cp.azure.domain.context.validators_factory_context import ValidatorsFactoryContext


class AccessKeyOperation(object):
    def __init__(self, key_pair_service, storage_service):
        """
        :param KeyPairService key_pair_service:
        :return:
        """
        self.key_pair_service = key_pair_service
        self.storage_service = storage_service

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_access_key(self, storage_client, group_name, validator_factory):
        """
        :param validator_factory:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return:
        """

        storage_accounts_list = self.storage_service.get_storage_per_resource_group(
            storage_client,
            group_name)

        validator_factory.try_validate(resource_type=StorageAccount, resource=storage_accounts_list)
        storage_account_name = storage_accounts_list[0].name

        # cloudshell.cp.azure.models.ssh_key.SSHKey instance
        ssh_key = self.key_pair_service.get_key_pair(storage_client=storage_client,
                                                     group_name=group_name,
                                                     storage_name=storage_account_name)

        return ssh_key.private_key
