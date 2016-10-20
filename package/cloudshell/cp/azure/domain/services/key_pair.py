from Crypto.PublicKey import RSA

from azure.storage.file import FileService

from cloudshell.cp.azure.models.ssh_key import SSHKey


class KeyPairService(object):
    FILE_SHARE_NAME = "sshkeypair"
    FILE_SHARE_DIRECTORY = ""
    SSH_PUB_KEY_NAME = "id_rsa.pub"
    SSH_PRIVATE_KEY_NAME = "id_rsa"

    def generate_key_pair(self, key_length=2048):
        """Generate SSH key pair model

        :param key_length: (int) SSH key length
        :return: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        """
        key = RSA.generate(key_length)
        pubkey = key.publickey()

        private_key = key.exportKey('PEM')
        public_key = pubkey.exportKey('OpenSSH')

        return SSHKey(private_key=private_key, public_key=public_key)

    def save_key_pair(self, account_key, key_pair, group_name, storage_name):
        """Save SSH key pair to the Azure storage

        :param account_key: (str) access key for storage account
        :param key_pair: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return:
        """
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

    def get_key_pair(self, account_key, group_name, storage_name):
        """Get SSH key pair from the Azure storage

        :param account_key: (str) access key for storage account
        :param group_name: (str) the name of the resource group on Azure
        :param storage_name: (str) the name of the storage on Azure
        :return: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        """
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
