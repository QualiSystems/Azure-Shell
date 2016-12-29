from unittest import TestCase

from mock import Mock

from cloudshell.cp.azure.domain.vm_management.operations.access_key_operation import AccessKeyOperation
from cloudshell.cp.azure.models.ssh_key import SSHKey


class TestAcessKeyOperation(TestCase):
    def setUp(self):
        self.key_pair_service = Mock()
        self.storage_service = Mock()
        self.access_key_operation = AccessKeyOperation(key_pair_service=self.key_pair_service,
                                                       storage_service=self.storage_service)

    def test_get_access_key_returns_public_key_only(self):
        # Arrange
        group_name = "group_name"
        storage_name = "storage_name"
        storage_client = Mock()
        ssh_key = SSHKey(private_key="private-key", public_key="public-key")
        self.storage_service.get_sandbox_storage_account_name = Mock(return_value=storage_name)
        self.key_pair_service.get_key_pair = Mock(return_value=ssh_key)

        # Act
        res = self.access_key_operation.get_access_key(storage_client, group_name)

        # Verify
        self.assertTrue(res == "private-key")
        self.key_pair_service.get_key_pair.assert_called_with(
                storage_client=storage_client,
                group_name=group_name,
                storage_name=storage_name)
