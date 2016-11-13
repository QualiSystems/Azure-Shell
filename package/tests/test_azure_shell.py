from unittest import TestCase

from mock import Mock

from cloudshell.cp.azure.azure_shell import AzureShell
from cloudshell.cp.azure.models.ssh_key import SSHKey


class TestAzureShell(TestCase):
    def setUp(self):
        self.azure_shell = AzureShell()
        self.command_context = Mock()

    def test_get_access_key_returns_public_key_only(self):
        # Arrange
        group_name = "group_name"
        storage_name = "storage_name"
        storage_client = Mock()
        ssh_key = SSHKey(private_key="private-key", public_key="public-key")
        self.azure_shell.key_pair_service.get_key_pair = Mock(return_value=ssh_key)

        # Act
        res = self.azure_shell.access_key_operation.get_access_key(storage_client, group_name, storage_name)

        # Verify
        self.assertTrue(res == "public-key")
        self.azure_shell.key_pair_service.get_key_pair.assert_called_with(
                                                    storage_client=storage_client,
                                                    group_name=group_name,
                                                    storage_name=storage_name)
