import random
import string

from azure.mgmt.compute.models import OperatingSystemTypes

from cloudshell.cp.azure.models.vm_credentials import VMCredentials
from cloudshell.cp.azure.models.authorized_key import AuthorizedKey


class VMCredentialsService(object):

    DEFAULT_LINUX_USERNAME = "adminuser"
    DEFAULT_WINDOWS_USERNAME = "adminuser"
    LINUX_PATH_TO_SSH_KEY = "/home/{username}/.ssh/authorized_keys"

    def _generate_password(self, length=10):
        """Generate password of the given length with digit and uppercase letter

        :param length: (int) password length
        :return: (str) generated password
        """
        # generate password with given length from the lowercase letters
        password = [random.choice(string.ascii_lowercase) for _ in xrange(length)]

        # add uppercase and digit symbol to the password
        rand_idxs = random.sample(xrange(length), 2)

        for idx, symbols_range in zip(rand_idxs, [string.ascii_uppercase, string.digits]):
            password[idx] = random.choice(symbols_range)

        return "".join(password)

    def prepare_credentials(self, os_type, username, password, storage_service, key_pair_service,
                            storage_client, group_name, storage_name):
        """ Prepare credentials for Windows/Linux VM

        :param os_type: azure.mgmt.compute.models.OperatingSystemTypes os type (linux/windows)
        :param username: VM username
        :param password: VM password
        :param storage_service: cloudshell.cp.azure.services.storage_service.StorageService instance
        :param key_pair_service: cloudshell.cp.azure.services.key_pair.KeyPairService instance
        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: resource group name (reservation id)
        :param storage_name: Azure storage name
        :return: VMCredentials instance
        :rtype: cloudshell.cp.azure.models.vm_credentials.VMCredentials
        """
        ssh_key = None

        if os_type is OperatingSystemTypes.linux:
            username, password, ssh_key = self._prepare_linux_credentials(
                username=username,
                password=password,
                storage_service=storage_service,
                key_pair_service=key_pair_service,
                storage_client=storage_client,
                group_name=group_name,
                storage_name=storage_name)
        else:
            username, password = self._prepare_windows_credentials(username, password)

        return VMCredentials(admin_username=username, admin_password=password, ssh_key=ssh_key)

    def _prepare_windows_credentials(self, username, password):
        """Prepare Windows credentials for the VM (generates password, set default user if credentials weren't provided)

        :param username: VM username
        :param password: VM password
        :return: (tuple) username and password
        """
        if not username:
            username = self.DEFAULT_WINDOWS_USERNAME
        if not password:
            password = self._generate_password()

        return username, password

    def _get_ssh_key(self, username, storage_service, key_pair_service, storage_client, group_name, storage_name):
        """Retrieve SSH key pair from Azure storage and return Azure SSH Key model

        :param username: VM username
        :param storage_service: cloudshell.cp.azure.services.storage_service.StorageService instance
        :param key_pair_service: cloudshell.cp.azure.services.key_pair.KeyPairService instance
        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: resource group name (reservation id)
        :param storage_name: Azure storage name
        :return: cloudshell.cp.azure.models.authorized_key.AuthorizedKey
        """
        key_pair = key_pair_service.get_key_pair(storage_client=storage_client,
                                                 group_name=group_name,
                                                 storage_name=storage_name)

        path_to_key = self.LINUX_PATH_TO_SSH_KEY.format(username=username)

        return AuthorizedKey(path_to_key, key_pair.public_key)

    def _prepare_linux_credentials(self, username, password, storage_service, key_pair_service, storage_client,
                                   group_name, storage_name):
        """Prepare Linux credentials for the VM (prepare SSH key, set default user if credentials weren't provided)

        :param username: VM username
        :param password: VM password
        :param storage_service: cloudshell.cp.azure.services.storage_service.StorageService instance
        :param key_pair_service: cloudshell.cp.azure.services.key_pair.KeyPairService instance
        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: resource group name (reservation id)
        :param storage_name: Azure storage name
        :return: (tuple) username, password and ssh_key
        """
        ssh_key = None

        if not username:
            username = self.DEFAULT_LINUX_USERNAME
        if not password:
            ssh_key = self._get_ssh_key(
                username=username,
                storage_service=storage_service,
                key_pair_service=key_pair_service,
                storage_client=storage_client,
                group_name=group_name,
                storage_name=storage_name)

        return username, password, ssh_key
