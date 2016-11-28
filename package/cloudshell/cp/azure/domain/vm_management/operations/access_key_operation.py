from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error


class AccessKeyOperation(object):
    def __init__(self, key_pair_service):
        """
        :param KeyPairService key_pair_service:
        :return:
        """
        self.key_pair_service = key_pair_service

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_access_key(self, storage_client, group_name, storage_name):
        """
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return:
        """

        # cloudshell.cp.azure.models.ssh_key.SSHKey instance
        ssh_key = self.key_pair_service.get_key_pair(storage_client=storage_client,
                                                     group_name=group_name,
                                                     storage_name=storage_name)

        return ssh_key.public_key  # only public key is returned to the client
