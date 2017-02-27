from unittest import TestCase

import mock

from cloudshell.cp.azure.common.parsers.rules_attribute_parser import RulesAttributeParser


class TestRulesAttributeParser(TestCase):
    def setUp(self):
        super(TestRulesAttributeParser, self).setUp()
        self.tested_class = RulesAttributeParser

    def test_parse_port_group_attribute(self):
        """Check that parser will parse string into list with three rules """
        test_rules_data = "80;443;200-220:udp"

        # Act
        with mock.patch.object(self.tested_class, "_single_port_parse"):
            parsed_rules = self.tested_class.parse_port_group_attribute(test_rules_data)

            # Verify
            self.assertIsInstance(parsed_rules, list)
            self.assertEqual(len(parsed_rules), 3)
            self.tested_class._single_port_parse.assert_called()

    def test_parse_port_group_attribute_with_delimiter_in_front_and_end(self):
        """Check that parser will parse string into list with three rules """
        test_rules_data = ";80;443;200-220:udp;"

        # Act
        with mock.patch.object(self.tested_class, "_single_port_parse"):
            parsed_rules = self.tested_class.parse_port_group_attribute(test_rules_data)

            # Verify
            self.assertIsInstance(parsed_rules, list)
            self.assertEqual(len(parsed_rules), 3)
            self.tested_class._single_port_parse.assert_called()

    @mock.patch("cloudshell.cp.azure.common.parsers.rules_attribute_parser.RuleData")
    def test_single_port_parse_ports_range_with_protocol(self, rule_data_class):
        """Check that method will return RuleData instance with correct attributes"""
        test_rule_data = "80-50000:udp"
        expected_rule = mock.MagicMock()
        rule_data_class.return_value = expected_rule

        # Act
        parsed_rule = self.tested_class._single_port_parse(test_rule_data)

        # Verify
        rule_data_class.assert_called_once_with(from_port='80', to_port='50000', protocol='udp')
        self.assertIs(parsed_rule, expected_rule)

    @mock.patch("cloudshell.cp.azure.common.parsers.rules_attribute_parser.RuleData")
    def test_single_port_parse_with_uppercase_protocol(self, rule_data_class):
        """Check that method will return RuleData instance with correct attributes when protocol is in upper case"""
        test_rule_data = "80:UDP"
        expected_rule = mock.MagicMock()
        rule_data_class.return_value = expected_rule

        # Act
        parsed_rule = self.tested_class._single_port_parse(test_rule_data)

        # Verify
        rule_data_class.assert_called_once_with(port='80', protocol='udp')
        self.assertIs(parsed_rule, expected_rule)

    @mock.patch("cloudshell.cp.azure.common.parsers.rules_attribute_parser.RuleData")
    def test_single_port_parse_single_port_with_protocol(self, rule_data_class):
        """Check that method will return RuleData instance with correct attributes"""
        test_rule_data = "80:udp"
        expected_rule = mock.MagicMock()
        rule_data_class.return_value = expected_rule

        # Act
        parsed_rule = self.tested_class._single_port_parse(test_rule_data)

        # Verify
        rule_data_class.assert_called_once_with(port='80', protocol='udp')
        self.assertIs(parsed_rule, expected_rule)

    @mock.patch("cloudshell.cp.azure.common.parsers.rules_attribute_parser.RuleData")
    def test_single_port_parse_ports_range_without_protocol(self, rule_data_class):
        """Check that method will return RuleData instance with correct attributes"""
        test_rule_data = "20-80"
        expected_rule = mock.MagicMock()
        rule_data_class.return_value = expected_rule

        # Act
        parsed_rule = self.tested_class._single_port_parse(test_rule_data)

        # Verify
        rule_data_class.assert_called_once_with(from_port='20', to_port='80', protocol='tcp')
        self.assertIs(parsed_rule, expected_rule)

    @mock.patch("cloudshell.cp.azure.common.parsers.rules_attribute_parser.RuleData")
    def test_single_port_parse_single_port_without_protocol(self, rule_data_class):
        """Check that method will return RuleData instance with correct attributes"""
        test_rule_data = "80"
        expected_rule = mock.MagicMock()
        rule_data_class.return_value = expected_rule

        # Act
        parsed_rule = self.tested_class._single_port_parse(test_rule_data)

        # Verify
        rule_data_class.assert_called_once_with(port='80', protocol='tcp')
        self.assertIs(parsed_rule, expected_rule)

    def test_single_port_parse_single_port_without_protocol(self):
        """Check that method will raise exception in case of invalid rule format"""
        test_rule_data = "incorrect_rule_format"

        with self.assertRaises(ValueError):
            self.tested_class._single_port_parse(test_rule_data)
