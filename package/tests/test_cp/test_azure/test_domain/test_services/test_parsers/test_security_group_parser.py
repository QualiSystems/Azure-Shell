from unittest import TestCase
from mock import *

from cloudshell.cp.azure.common.parsers.security_group_parser import SecurityGroupParser
from cloudshell.cp.azure.models.app_security_groups_model import SecurityGroupConfiguration


class TestRulesAttributeParser(TestCase):
    def test_parse_security_group_configurations_returns_none_when_missing_data(self):
        """
        if pass a none list or empty data, result will be None
        """
        parser = SecurityGroupParser()
        result = parser.parse_security_group_configurations(None)
        self.assertTrue(result is None)

    def test_parse_security_group_configurations(self):
        """
        if pass a none list or empty data, result will be None
        """
        parser = SecurityGroupParser()
        data = [Mock()]
        result = parser.parse_security_group_configurations(data)
        self.assertTrue(len(result) == 1)
        self.assertTrue(isinstance(result[0], SecurityGroupConfiguration))

