from threading import Lock
from unittest import TestCase

from azure.mgmt.network.models import NetworkSecurityGroup
import mock
from mock import MagicMock
from mock import Mock

from cloudshell.cp.azure.domain.services.security_group import SecurityGroupService
from cloudshell.cp.azure.models.rule_data import RuleData
from azure.mgmt.network.models import RouteNextHopType


class TestSecurityGroupService(TestCase):
    def setUp(self):
        self.network_service = MagicMock()
        self.security_group_service = SecurityGroupService(self.network_service)
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
        rule_data = mock.MagicMock(spec=RuleData)
        rule_data.port = 5
        rule_data.protocol = 'tcp'
        rule_data.access = "Allow"
        rule_data.name = "New security rule"
        private_vm_ip = mock.MagicMock()
        priority = mock.MagicMock()

        # Act
        prepared_rule = self.security_group_service._prepare_security_group_rule(
            rule_data=rule_data,
            destination_address=private_vm_ip,
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
            destination_addr=private_vm_ip,
            lock=MagicMock())

        # Verify
        self.security_group_service._prepare_security_group_rule.assert_called_once_with(
            priority=self.security_group_service.RULE_DEFAULT_PRIORITY,
            destination_address=private_vm_ip,
            rule_data=rule_data,
            source_address=RouteNextHopType.internet)

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
            destination_addr=private_vm_ip,
            lock=MagicMock())

        # Verify
        self.security_group_service._prepare_security_group_rule.assert_called_once_with(
            priority=self.security_group_service.RULE_DEFAULT_PRIORITY,
            destination_address=private_vm_ip,
            rule_data=rule_data,
            source_address=RouteNextHopType.internet)

        self.network_client.security_rules.create_or_update.assert_called_with(
            network_security_group_name=self.security_group_name,
            resource_group_name=self.group_name,
            security_rule_name=rule_model.name,
            security_rule_parameters=rule_model)

    def test_get_network_security_group(self):
        # Arrange
        self.network_security_group = MagicMock()
        self.security_group_service.list_network_security_group = MagicMock()
        self.security_group_service.list_network_security_group.return_value = [self.network_security_group]

        # Act
        self.security_group_service.get_first_network_security_group(self.network_client, self.group_name)

        # Verify
        self.security_group_service.list_network_security_group.assert_called_once_with(
            network_client=self.network_client,
            group_name=self.group_name)

    def test_delete_security_rules(self):
        # Arrange
        self.network_security_group = MagicMock()
        network_client = MagicMock()
        private_ip_address = Mock()
        resource_group_name = "group_name"
        vm_name = "vm_name"
        security_group = NetworkSecurityGroup()
        security_group.name = "security_group_name"
        security_rule = Mock()
        security_rule.name = "rule_name"
        security_rule.destination_address_prefix = private_ip_address
        security_rules = [security_rule]
        security_group.security_rules = security_rules
        self.security_group_service.get_first_network_security_group = MagicMock()
        self.security_group_service.get_first_network_security_group.return_value = security_group
        self.network_service.get_private_ip = Mock(return_value=private_ip_address)

        contex_enter_mock = Mock()
        locker = Mock()
        locker.__enter__ = contex_enter_mock
        locker.__exit__ = Mock()

        # Act
        self.security_group_service.delete_security_rules(network_client, resource_group_name, vm_name, locker, Mock())

        # Verify
        network_client.security_rules.delete.assert_called_once_with(
            resource_group_name=resource_group_name,
            network_security_group_name=security_group.name,
            security_rule_name=security_rule.name)
        contex_enter_mock.assert_called_once()
