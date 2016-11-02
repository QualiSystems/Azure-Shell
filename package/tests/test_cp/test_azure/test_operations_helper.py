from unittest import TestCase

from cloudshell.cp.azure.common.operations_helper import OperationsHelper


class test_operations_helper(TestCase):
    def test_operations_helper_generate_name(self):
        oh = OperationsHelper()
        base_name = "name"
        name = oh.generate_name(base_name)
        self.assertTrue(len(base_name) < len(name))
