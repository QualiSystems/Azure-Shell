from unittest import TestCase

import mock
from azure.mgmt.storage.models import StorageAccountCreateParameters
from mock import MagicMock
from mock import Mock
from msrestazure.azure_operation import AzureOperationPoller

from cloudshell.cp.azure.domain.services.key_pair import KeyPairService
from cloudshell.cp.azure.domain.services.security_group import SecurityGroupService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from tests.helpers.test_helper import TestHelper


class TestStorageService(TestCase):
    def setUp(self):
        self.storage_service = StorageService()
        self.group_name = "test_group_name"
        self.storage_name = "teststoragename"
        self.storage_client = mock.MagicMock()

    def test_create_storage_account(self):
        # Arrange
        region = "a region"
        account_name = "account name"
        tags = {}
        group_name = "a group name"

        storage_client = MagicMock()
        storage_client.storage_accounts.create = MagicMock()
        kind_storage_value = MagicMock()
        # Act

        self.storage_service.create_storage_account(storage_client, group_name, region, account_name, tags)

        # Verify
        storage_client.storage_accounts.create.assert_called_with(group_name, account_name,
                                                                  StorageAccountCreateParameters(
                                                                      sku=MagicMock(),
                                                                      kind=kind_storage_value,
                                                                      location=region,
                                                                      tags=tags),
                                                                  raw=False)

    def test_create_storage_account_wait_for_result(self):
        # Arrange
        storage_accounts_create = AzureOperationPoller(Mock(), Mock(), Mock())
        storage_accounts_create.wait = Mock()
        storage_client = MagicMock()
        storage_client.storage_accounts.create = Mock(return_value=storage_accounts_create)
        region = "a region"
        account_name = "account name"
        tags = {}
        group_name = "a group name"
        wait_until_created = True

        # Act
        self.storage_service.create_storage_account(storage_client, group_name, region, account_name, tags, wait_until_created)

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(storage_accounts_create.wait))

    def test_get_storage_per_resource_group(self):
        # Arrange
        storage_client = Mock()
        group_name = "a group name"
        storage_client.storage_accounts.list_by_resource_group = Mock(return_value=[])

        # Act
        result = self.storage_service.get_storage_per_resource_group(
            storage_client,
            group_name
        )

        # Verify
        self.assertTrue(isinstance(result, list))

    def test_get_storage_account_key(self):
        """Check that method uses storage client to retrieve first access key for the storage account"""
        storage_key = mock.MagicMock()

        self.storage_client.storage_accounts.list_keys.return_value = mock.MagicMock(keys=[storage_key])

        key = self.storage_service.get_storage_account_key(
            storage_client=self.storage_client,
            group_name=self.group_name,
            storage_name=self.storage_name)

        self.assertEqual(key, storage_key.value)


class TestVMService(TestCase):
    def setUp(self):
        self.vm_service = VirtualMachineService()

    def test_vm_service_create_vm(self):
        mock = MagicMock()
        compute_management_client = mock
        group_name = mock
        vm_name = mock
        region = 'a region'
        tags = {}
        compute_management_client.virtual_machines = mock
        compute_management_client.virtual_machines.create_or_update = MagicMock(return_value=mock)
        vm = 'some returned vm'
        self.vm_service._get_virtual_machine = MagicMock(return_value=vm)

        # Act
        self.vm_service.create_vm(compute_management_client=compute_management_client,
                                  image_offer=mock,
                                  image_publisher=mock,
                                  image_sku=mock,
                                  image_version=mock,
                                  admin_password=mock,
                                  admin_username=mock,
                                  computer_name=mock,
                                  group_name=group_name,
                                  nic_id=mock,
                                  region=region,
                                  storage_name=mock,
                                  vm_name=vm_name,
                                  tags=tags,
                                  instance_type=mock)

        # Verify
        compute_management_client.virtual_machines.create_or_update.assert_called_with(group_name, vm_name, vm)

    def test_vm_service_create_resource_group(self):
        # Arrange
        resource_management_client = MagicMock()
        resource_management_client.resource_groups.create_or_update = MagicMock(return_value="A test group")

        # Act
        region = 'region'
        group_name = MagicMock()
        tags = {}
        self.vm_service.create_resource_group(resource_management_client=resource_management_client,
                                              region=region,
                                              group_name=group_name, tags=tags)

        # Verify
        from azure.mgmt.resource.resources.models import ResourceGroup
        resource_management_client.resource_groups.create_or_update(group_name,
                                                                    ResourceGroup(location=region, tags=tags))

    def test_start_vm(self):
        """Check that method calls azure client to start VM action and returns it result"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        res = self.vm_service.start_vm(compute_management_client, group_name, vm_name)

        compute_management_client.virtual_machines.start.assert_called_with(resource_group_name=group_name,
                                                                            vm_name=vm_name)

        self.assertEqual(res, compute_management_client.virtual_machines.start().result())

    def test_stop_vm(self):
        """Check that method calls azure client to stop VM action and returns it result"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        res = self.vm_service.stop_vm(compute_management_client, group_name, vm_name)

        compute_management_client.virtual_machines.power_off.assert_called_with(resource_group_name=group_name,
                                                                                vm_name=vm_name)

        self.assertEqual(res, compute_management_client.virtual_machines.power_off().result())

    def test_start_vm_with_async_mode_true(self):
        """Check that method calls azure client to start VM action and doesn't wait for it result"""
        compute_management_client = MagicMock()
        operation_poller = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"
        compute_management_client.virtual_machines.power_off.return_value = operation_poller

        res = self.vm_service.start_vm(compute_management_client, group_name, vm_name, async=True)

        operation_poller.result.assert_not_called()
        self.assertIsNone(res)

    def test_stop_vm_with_async_mode_true(self):
        """Check that method calls azure client to stop VM action and doesn't wait for it result"""
        compute_management_client = MagicMock()
        operation_poller = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"
        compute_management_client.virtual_machines.power_off.return_value = operation_poller

        res = self.vm_service.stop_vm(compute_management_client, group_name, vm_name, async=True)

        operation_poller.result.assert_not_called()
        self.assertIsNone(res)


class TestKeyPairService(TestCase):
    def setUp(self):
        self.key_pair_service = KeyPairService()
        self.group_name = "test_group_name"
        self.storage_name = "teststoragename"
        self.account_key = "test_account_key"
        self.storage_client = mock.MagicMock()

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.RSA")
    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.SSHKey")
    def test_generate_key_pair(self, ssh_key_class, rsa_module):
        """Check that method uses RSA module to generate key pair and returns SSHKey model"""
        ssh_key_class.return_value = ssh_key_mock = mock.MagicMock()

        ssh_key = self.key_pair_service.generate_key_pair()

        ssh_key_class.assert_called_with(private_key=rsa_module.generate().exportKey(),
                                         public_key=rsa_module.generate().publickey().exportKey())
        self.assertIs(ssh_key, ssh_key_mock)

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.FileService")
    def test_save_key_pair(self, file_service_class):
        """Check that method uses storage client to save key pair to the Azure"""
        key_pair = mock.MagicMock()
        file_service = mock.MagicMock()
        file_service_class.return_value = file_service

        self.key_pair_service.save_key_pair(
            account_key=self.account_key,
            key_pair=key_pair,
            group_name=self.group_name,
            storage_name=self.storage_name)

        file_service_class.assert_called_once_with(account_key=self.account_key, account_name=self.storage_name)
        file_service.create_share.assert_called_once_with(self.key_pair_service.FILE_SHARE_NAME)

        file_service.create_file_from_bytes.assert_any_call(share_name=self.key_pair_service.FILE_SHARE_NAME,
                                                            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
                                                            file_name=self.key_pair_service.SSH_PUB_KEY_NAME,
                                                            file=key_pair.public_key)

        file_service.create_file_from_bytes.assert_any_call(share_name=self.key_pair_service.FILE_SHARE_NAME,
                                                            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
                                                            file_name=self.key_pair_service.SSH_PRIVATE_KEY_NAME,
                                                            file=key_pair.private_key)

    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.SSHKey")
    @mock.patch("cloudshell.cp.azure.domain.services.key_pair.FileService")
    def test_get_key_pair(self, file_service_class, ssh_key_class):
        """Check that method uses storage client to retrieve key pair from the Azure"""
        file_service = mock.MagicMock()
        file_service_class.return_value = file_service
        ssh_key_class.return_value = mocked_key_pair = mock.MagicMock()

        key_pair = self.key_pair_service.get_key_pair(
            account_key=self.account_key,
            group_name=self.group_name,
            storage_name=self.storage_name)

        file_service_class.assert_called_once_with(account_key=self.account_key, account_name=self.storage_name)

        file_service.get_file_to_bytes.assert_any_call(
            share_name=self.key_pair_service.FILE_SHARE_NAME,
            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
            file_name=self.key_pair_service.SSH_PUB_KEY_NAME)

        file_service.get_file_to_bytes.assert_any_call(
            share_name=self.key_pair_service.FILE_SHARE_NAME,
            directory_name=self.key_pair_service.FILE_SHARE_DIRECTORY,
            file_name=self.key_pair_service.SSH_PRIVATE_KEY_NAME)

        self.assertIs(key_pair, mocked_key_pair)


class TestSecurityGroupService(TestCase):
    def setUp(self):
        self.security_group_service = SecurityGroupService()
        self.group_name = "test_group_name"
        self.security_group_name = "teststoragename"
        self.network_client = mock.MagicMock()

    def test_rule_priority_generator(self):
        """Check that method creates generator started from the given value plus increase step"""
        expected_values = [
            self.security_group_service.RULE_DEFAULT_PRIORITY,
            (self.security_group_service.RULE_DEFAULT_PRIORITY +
             self.security_group_service.RULE_PRIORITY_INCREASE_STEP),
            (self.security_group_service.RULE_DEFAULT_PRIORITY +
             self.security_group_service.RULE_PRIORITY_INCREASE_STEP * 2),
            (self.security_group_service.RULE_DEFAULT_PRIORITY +
             self.security_group_service.RULE_PRIORITY_INCREASE_STEP * 3)]

        # Act
        generator = self.security_group_service._rule_priority_generator([])

        # Verify
        generated_values = [next(generator) for _ in xrange(4)]
        self.assertEqual(expected_values, generated_values)

    def test_list_network_security_group(self):
        """Check that method calls azure network client to get list of NSGs and converts them into list"""
        # Act
        security_groups = self.security_group_service.list_network_security_group(
            network_client=self.network_client,
            group_name=self.group_name)

        # Verify
        self.network_client.network_security_groups.list.assert_called_once_with(self.group_name)
        self.assertIsInstance(security_groups, list)

    @mock.patch("cloudshell.cp.azure.domain.services.security_group.NetworkSecurityGroup")
    def test_create_network_security_group(self, nsg_class):
        """Check that method calls azure network client to create NSG and returns it result"""
        region = mock.MagicMock()
        tags = mock.MagicMock()
        nsg_class.return_value = nsg_model = mock.MagicMock()

        # Act
        nsg = self.security_group_service.create_network_security_group(
            network_client=self.network_client,
            group_name=self.group_name,
            security_group_name=self.security_group_name,
            region=region,
            tags=tags)

        # Verify
        self.network_client.network_security_groups.create_or_update.assert_called_once_with(
            resource_group_name=self.group_name,
            network_security_group_name=self.security_group_name,
            parameters=nsg_model)

        self.assertEqual(nsg, self.network_client.network_security_groups.create_or_update().result())

    @mock.patch("cloudshell.cp.azure.domain.services.security_group.SecurityRule")
    def test_prepare_security_group_rule(self, security_rule_class):
        """Check that method returns SecurityRule model"""
        security_rule_class.return_value = security_rule = mock.MagicMock()
        rule_data = mock.MagicMock()
        private_vm_ip = mock.MagicMock()
        priority = mock.MagicMock()

        # Act
        prepared_rule = self.security_group_service._prepare_security_group_rule(
            rule_data=rule_data,
            destination_addr=private_vm_ip,
            priority=priority)

        # Verify
        self.assertEqual(prepared_rule, security_rule)

    def test_create_network_security_group_rules_without_existing_rules(self):
        """Check that method will call network_client for NSG rules creation starting from default priority"""
        rule_data = mock.MagicMock()
        inbound_rules = [rule_data]
        private_vm_ip = mock.MagicMock()
        rule_model = mock.MagicMock()
        self.network_client.security_rules.list.return_value = []
        self.security_group_service._prepare_security_group_rule = mock.MagicMock(return_value=rule_model)

        # Act
        self.security_group_service.create_network_security_group_rules(
            network_client=self.network_client,
            group_name=self.group_name,
            security_group_name=self.security_group_name,
            inbound_rules=inbound_rules,
            destination_addr=private_vm_ip)

        # Verify
        self.security_group_service._prepare_security_group_rule.assert_called_once_with(
            priority=self.security_group_service.RULE_DEFAULT_PRIORITY,
            destination_addr=private_vm_ip,
            rule_data=rule_data)

        self.network_client.security_rules.create_or_update.assert_called_with(
            network_security_group_name=self.security_group_name,
            resource_group_name=self.group_name,
            security_rule_name=rule_model.name,
            security_rule_parameters=rule_model)

    def test_create_network_security_group_rules_with_existing_rules(self):
        """Check that method will call network_client for NSG rules creation starting from first available priority"""
        rule_data = mock.MagicMock()
        inbound_rules = [rule_data]
        private_vm_ip = mock.MagicMock()
        rule_model = mock.MagicMock()

        self.network_client.security_rules.list.return_value = [
            mock.MagicMock(priority=5000),
            mock.MagicMock(priority=100500),
            mock.MagicMock(priority=100000)]

        self.security_group_service._prepare_security_group_rule = mock.MagicMock(return_value=rule_model)

        # Act
        self.security_group_service.create_network_security_group_rules(
            network_client=self.network_client,
            group_name=self.group_name,
            security_group_name=self.security_group_name,
            inbound_rules=inbound_rules,
            destination_addr=private_vm_ip)

        # Verify
        self.security_group_service._prepare_security_group_rule.assert_called_once_with(
            priority=self.security_group_service.RULE_DEFAULT_PRIORITY,
            destination_addr=private_vm_ip,
            rule_data=rule_data)

        self.network_client.security_rules.create_or_update.assert_called_with(
            network_security_group_name=self.security_group_name,
            resource_group_name=self.group_name,
            security_rule_name=rule_model.name,
            security_rule_parameters=rule_model)
