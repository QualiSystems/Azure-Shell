from threading import Lock

from Crypto.PublicKey import RSA

from cloudshell.cp.azure.models.ssh_key import SSHKey


class KeyPairService(object):
    FILE_SHARE_NAME = "sshkeypair"
    FILE_SHARE_DIRECTORY = ""
    SSH_PUB_KEY_NAME = "id_rsa.pub"
    SSH_PRIVATE_KEY_NAME = "id_rsa"

    def __init__(self, storage_service):
        """
        :param storage_service: cloudshell.cp.azure.domain.services.storage_service.StorageService instance
        """
        self._storage_service = storage_service
        self._key_pair_lock = Lock()
        self._cached_key_pairs = {}

    def generate_key_pair(self, key_length=2048):
        """
        Generate SSH key pair model

        :param key_length: (int) SSH key length
        :return: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        """
        key = RSA.generate(key_length)
        pubkey = key.publickey()

        private_key = key.exportKey('PEM')
        public_key = pubkey.exportKey('OpenSSH')

        return SSHKey(private_key=private_key, public_key=public_key)

    def save_key_pair(self, storage_client, group_name, storage_name, key_pair):
        """
        Save SSH key pair to the Azure storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :param key_pair: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        :return:
        """
        self._storage_service.create_file(
            storage_client=storage_client,
            group_name=group_name,
            storage_name=storage_name,
            share_name=self.FILE_SHARE_NAME,
            directory_name=self.FILE_SHARE_DIRECTORY,
            file_name=self.SSH_PUB_KEY_NAME,
            file_content=key_pair.public_key)

        self._storage_service.create_file(
            storage_client=storage_client,
            group_name=group_name,
            storage_name=storage_name,
            share_name=self.FILE_SHARE_NAME,
            directory_name=self.FILE_SHARE_DIRECTORY,
            file_name=self.SSH_PRIVATE_KEY_NAME,
            file_content=key_pair.private_key)

    def get_key_pair(self, storage_client, group_name, storage_name):
        """
        Get SSH key pair from the Azure storage

        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        """
        cached_key = (group_name, storage_name)

        if cached_key not in self._cached_key_pairs:
            with self._key_pair_lock:
                ssh_key = self._cached_key_pairs.get(cached_key)

                if ssh_key is None:
                    pub_key_file = self._storage_service.get_file(
                        storage_client=storage_client,
                        group_name=group_name,
                        storage_name=storage_name,
                        share_name=self.FILE_SHARE_NAME,
                        directory_name=self.FILE_SHARE_DIRECTORY,
                        file_name=self.SSH_PUB_KEY_NAME)

                    private_key_file = self._storage_service.get_file(
                        storage_client=storage_client,
                        group_name=group_name,
                        storage_name=storage_name,
                        share_name=self.FILE_SHARE_NAME,
                        directory_name=self.FILE_SHARE_DIRECTORY,
                        file_name=self.SSH_PRIVATE_KEY_NAME)

                    self._cached_key_pairs[cached_key] = SSHKey(private_key=private_key_file.content,
                                                                public_key=pub_key_file.content)

        return self._cached_key_pairs[cached_key]
