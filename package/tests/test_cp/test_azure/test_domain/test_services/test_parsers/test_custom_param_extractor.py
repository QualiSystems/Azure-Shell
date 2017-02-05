from unittest import TestCase

import mock

from cloudshell.cp.azure.common.parsers.custom_param_extractor import VmCustomParamsExtractor


class TestRulesAttributeParser(TestCase):
    def setUp(self):
        self.vm_custom_params_extractor = VmCustomParamsExtractor()

    def test_get_custom_param_value(self):
        """Check that method will find correct parameter by it's name"""
        parameter_name = "test_parameter_key_name"
        sought_parameter = mock.MagicMock()
        sought_parameter.name = parameter_name
        custom_params = [mock.MagicMock(), sought_parameter, mock.MagicMock()]

        # Act
        result = self.vm_custom_params_extractor.get_custom_param_value(custom_params=custom_params,
                                                                        name=parameter_name)

        # Verify
        self.assertEqual(result, sought_parameter.value)

    def test_get_custom_param_value_no_value(self):
        """Check that method will return None in case parameter wasn't found"""
        parameter_name = "test_parameter_key_name"
        custom_params = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock()]

        # Act
        result = self.vm_custom_params_extractor.get_custom_param_value(custom_params=custom_params,
                                                                        name=parameter_name)

        # Verify
        self.assertIsNone(result)
