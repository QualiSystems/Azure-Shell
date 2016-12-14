from unittest import TestCase

import mock
from mock import MagicMock

from cloudshell.cp.azure.domain.services.key_pair import KeyPairService


class TestKeyPairService(TestCase):
    def setUp(self):
        self.group_name = "test_group_name"
        self.storage_name = "teststoragename"
        self.account_key = "test_account_key"
        self.storage_service = MagicMock()
        self.key_pair_service = KeyPairService(storage_service=self.storage_service)

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.RSA")
    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.SSHKey")
    def test_generate_key_pair(self, ssh_key_class, rsa_module):
        """Check that method uses RSA module to generate key pair and returns SSHKey model"""
        ssh_key_class.return_value = ssh_key_mock = mock.MagicMock()

        ssh_key = self.key_pair_service.generate_key_pair()

        ssh_key_class.assert_called_with(private_key=rsa_module.generate().exportKey(),
                                         public_key=rsa_module.generate().publickey().exportKey())
        self.assertIs(ssh_key, ssh_key_mock)

    def test_save_key_pair(self):
        """Check that method uses storage service to save key pair to the Azure"""
        key_pair = MagicMock()
        storage_client = MagicMock()

        # Act
        self.key_pair_service.save_key_pair(
                storage_client=storage_client,
                group_name=self.group_name,
                storage_name=self.storage_name,
                key_pair=key_pair)

        # Verify
        self.key_pair_service._storage_service.create_file.assert_any_call(
                storage_client=storage_client,
                group_name=self.group_name,
                storage_name=self.storage_name,
                share_name=self.key_pair_service.FILE_SHARE_NAME,
                directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
                file_name=self.key_pair_service.SSH_PUB_KEY_NAME,
                file_content=key_pair.public_key)

        self.key_pair_service._storage_service.create_file.assert_any_call(
                storage_client=storage_client,
                group_name=self.group_name,
                storage_name=self.storage_name,
                share_name=self.key_pair_service.FILE_SHARE_NAME,
                directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
                file_name=self.key_pair_service.SSH_PRIVATE_KEY_NAME,
                file_content=key_pair.private_key)

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.SSHKey")
    def test_get_key_pair(self, ssh_key_class):
        """Check that method uses storage service to retrieve key pair from the Azure"""
        storage_client = MagicMock()
        mocked_ssh_key = MagicMock()
        ssh_key_class.return_value = mocked_ssh_key

        # Act
        key_pair = self.key_pair_service.get_key_pair(
                storage_client=storage_client,
                group_name=self.group_name,
                storage_name=self.storage_name)

        # Verify
        self.key_pair_service._storage_service.get_file.assert_any_call(
                storage_client=storage_client,
                group_name=self.group_name,
                storage_name=self.storage_name,
                share_name=self.key_pair_service.FILE_SHARE_NAME,
                directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
                file_name=self.key_pair_service.SSH_PUB_KEY_NAME)

        self.key_pair_service._storage_service.get_file.assert_any_call(
                storage_client=storage_client,
                group_name=self.group_name,
                storage_name=self.storage_name,
                share_name=self.key_pair_service.FILE_SHARE_NAME,
                directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
                file_name=self.key_pair_service.SSH_PRIVATE_KEY_NAME)

        self.assertEqual(key_pair, mocked_ssh_key)
