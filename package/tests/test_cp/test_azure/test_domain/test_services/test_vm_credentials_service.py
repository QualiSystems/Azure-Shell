from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.services.vm_credentials_service import VMCredentialsService
from cloudshell.cp.azure.models.vm_credentials import VMCredentials


class TestVMCredentialsService(TestCase):
    def setUp(self):
        self.test_username = "test_username"
        self.test_password = "testPassword123"
        self.test_group_name = "test_username"
        self.test_storage_name = "test_storage_name"
        self.test_storage_service = mock.MagicMock()
        self.test_key_pair_service = mock.MagicMock()
        self.test_storage_client = mock.MagicMock()
        self.vm_credentials = VMCredentialsService()

    def test_generate_password(self):
        """Check that method will generate password with given length and with digit and uppercase letter"""
        # Act
        password = self.vm_credentials._generate_password(19)

        # Verify
        self.assertEqual(len(password), 19)
        self.assertTrue(any(char.isdigit() for char in password),
                        msg="Generated password must contain at least one digit character")

        self.assertTrue(any(char.isupper() for char in password),
                        msg="Generated password must contain at least one uppercase character")

    @mock.patch("cloudshell.cp.azure.domain.services.vm_credentials_service.AuthorizedKey")
    def test_get_ssh_key(self, authorized_key_class):
        """Check that method will return cloudshell.cp.azure.models.authorized_key.AuthorizedKey instance"""
        authorized_key_class.return_value = authorized_key = mock.MagicMock()

        ssh_key = self.vm_credentials._get_ssh_key(
                username=self.test_username,
                storage_service=self.test_storage_service,
                key_pair_service=self.test_key_pair_service,
                storage_client=self.test_storage_client,
                group_name=self.test_group_name,
                storage_name=self.test_storage_name)

        self.assertIs(ssh_key, authorized_key)

    @mock.patch("cloudshell.cp.azure.domain.services.vm_credentials_service.OperatingSystemTypes")
    def test_prepare_credentials_with_windows_os_type(self, os_types):
        """Check that method will call _prepare_windows_credentials and return VMCredentials model instance"""
        self.vm_credentials._prepare_windows_credentials = mock.MagicMock(return_value=(self.test_username,
                                                                                        self.test_password))

        vm_creds = self.vm_credentials.prepare_credentials(
                os_type=os_types.windows,
                username=self.test_username,
                password=self.test_password,
                storage_service=self.test_storage_service,
                key_pair_service=self.test_key_pair_service,
                storage_client=self.test_storage_client,
                group_name=self.test_group_name,
                storage_name=self.test_storage_name)

        self.vm_credentials._prepare_windows_credentials.assert_called_once_with(self.test_username, self.test_password)
        self.assertIsInstance(vm_creds, VMCredentials)

    @mock.patch("cloudshell.cp.azure.domain.services.vm_credentials_service.OperatingSystemTypes")
    def test_prepare_credentials_with_linux_os_type(self, os_types):
        """Check that method will call _prepare_linux_credentials and return VMCredentials model instance"""
        # from azure.mgmt.compute.models import OperatingSystemTypes
        self.vm_credentials._prepare_linux_credentials = mock.MagicMock(return_value=(self.test_username,
                                                                                      self.test_password,
                                                                                      mock.MagicMock()))
        vm_creds = self.vm_credentials.prepare_credentials(
                os_type=os_types.linux,
                username=self.test_username,
                password=self.test_password,
                storage_service=self.test_storage_service,
                key_pair_service=self.test_key_pair_service,
                storage_client=self.test_storage_client,
                group_name=self.test_group_name,
                storage_name=self.test_storage_name)

        self.vm_credentials._prepare_linux_credentials.assert_called_once_with(
                username=self.test_username,
                password=self.test_password,
                storage_service=self.test_storage_service,
                key_pair_service=self.test_key_pair_service,
                storage_client=self.test_storage_client,
                group_name=self.test_group_name,
                storage_name=self.test_storage_name)

        self.assertIsInstance(vm_creds, VMCredentials)

    def test_prepare_windows_credentials(self):
        """Check that method will return same credentials if username and password were provided"""
        username, password = self.vm_credentials._prepare_windows_credentials(self.test_username, self.test_password)

        self.assertEqual(username, self.test_username)
        self.assertEqual(password, self.test_password)

    def test_prepare_windows_credentials_without_user_and_password(self):
        """Check that method will return default username and generate password if credentials weren't provided"""
        generated_pass = mock.MagicMock()
        self.vm_credentials._generate_password = mock.MagicMock(return_value=generated_pass)

        username, password = self.vm_credentials._prepare_windows_credentials("", "")

        self.assertEqual(username, self.vm_credentials.DEFAULT_WINDOWS_USERNAME)
        self.assertEqual(password, generated_pass)

    def test_prepare_linux_credentials(self):
        """Check that method will return same credentials if username and password were provided"""
        username, password, ssh_key = self.vm_credentials._prepare_linux_credentials(
                username=self.test_username,
                password=self.test_password,
                storage_service=self.test_storage_service,
                key_pair_service=self.test_key_pair_service,
                storage_client=self.test_storage_client,
                group_name=self.test_group_name,
                storage_name=self.test_storage_name)

        self.assertEqual(username, self.test_username)
        self.assertEqual(password, self.test_password)
        self.assertIsNone(ssh_key)

    def test_prepare_linux_credentials_without_user_and_password(self):
        """Check that method will return default username and ssh_key if credentials weren't provided"""
        returned_ssh_key = mock.MagicMock()
        self.vm_credentials._get_ssh_key = mock.MagicMock(return_value=returned_ssh_key)

        username, password, ssh_key = self.vm_credentials._prepare_linux_credentials(
                username="",
                password="",
                storage_service=self.test_storage_service,
                key_pair_service=self.test_key_pair_service,
                storage_client=self.test_storage_client,
                group_name=self.test_group_name,
                storage_name=self.test_storage_name)

        self.assertEqual(username, self.vm_credentials.DEFAULT_LINUX_USERNAME)
        self.assertEqual(password, "")
        self.assertEqual(ssh_key, returned_ssh_key)
