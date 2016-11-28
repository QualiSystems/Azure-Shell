from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.vm_management.operations.app_ports_operation import DeployedAppPortsOperation


class TestDeployedAppPortsOperation(TestCase):
    def setUp(self):
        self.custom_params = mock.MagicMock()
        self.vm_custom_params_extractor = mock.MagicMock()
        self.logger = mock.MagicMock()
        self.app_ports_operation = DeployedAppPortsOperation(
            vm_custom_params_extractor=self.vm_custom_params_extractor)

    @mock.patch("cloudshell.cp.azure.domain.vm_management.operations.app_ports_operation.RulesAttributeParser")
    def test_get_formated_deployed_app_ports(self, rules_attribute_parser):
        """Check that method will call _port_rule_to_string method for each rule"""
        custom_param_value = mock.MagicMock()
        self.vm_custom_params_extractor.get_custom_param_value.return_value = custom_param_value
        first_rule = mock.MagicMock()
        second_rule = mock.MagicMock()
        parsed_rules = [first_rule, second_rule]
        rules_attribute_parser.parse_port_group_attribute.return_value = parsed_rules
        self.app_ports_operation._port_rule_to_string = mock.MagicMock(return_value="")

        # Act
        self.app_ports_operation.get_formated_deployed_app_ports(self.custom_params)

        # Verify
        self.vm_custom_params_extractor.get_custom_param_value.assert_called_once_with(
            self.custom_params, "inbound_ports")
        rules_attribute_parser.parse_port_group_attribute.assert_called_once_with(custom_param_value)

        self.app_ports_operation._port_rule_to_string.assert_any_call(first_rule)
        self.app_ports_operation._port_rule_to_string.assert_any_call(second_rule)

    @mock.patch("cloudshell.cp.azure.domain.vm_management.operations.app_ports_operation.RulesAttributeParser")
    def test_get_formated_deployed_app_ports_no_inbound_ports(self, rules_attribute_parser):
        """Check that method will not parse rules if "inbound_ports" attribute is empty"""
        self.vm_custom_params_extractor.get_custom_param_value.return_value = ""

        # Act
        self.app_ports_operation.get_formated_deployed_app_ports(self.custom_params)

        # Verify
        self.vm_custom_params_extractor.get_custom_param_value.assert_called_once_with(
            self.custom_params, "inbound_ports")
        rules_attribute_parser.parse_port_group_attribute.assert_not_called()

    def test_port_rule_to_string_parses_single_port(self):
        """Check that method will correctly parse model with a single port into string"""
        port = "test_port"
        protocol = "test_protocol"
        port_rule = mock.MagicMock(port=port, protocol=protocol)
        expected_str = "Port {} {}".format(port, protocol)

        # Act
        res = self.app_ports_operation._port_rule_to_string(port_rule)

        # Verify
        self.assertEqual(res, expected_str)

    def test_port_rule_to_string_parses_port_range(self):
        """Check that method will correctly parse model with port range into string"""
        from_port = "test_port_from"
        to_port = "test_port_from"
        protocol = "test_protocol"
        port_rule = mock.MagicMock(port=None, from_port=from_port, to_port=to_port, protocol=protocol)
        expected_str = "Ports {}-{} {}".format(to_port, from_port, protocol)

        # Act
        res = self.app_ports_operation._port_rule_to_string(port_rule)

        # Verify
        self.assertEqual(res, expected_str)
