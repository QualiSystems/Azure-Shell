from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.services.parsers.command_result_parser import CommandResultsParser


class TestCommandResultsParser(TestCase):
    def setUp(self):
        self.command_result_parser = CommandResultsParser()

    @mock.patch("cloudshell.cp.azure.domain.services.parsers.command_result_parser.jsonpickle")
    def test_set_command_result(self, jsonpickle):
        """Check that method will convert result to string"""
        test_result = mock.MagicMock()
        unpicklable = mock.MagicMock()

        # Act
        result = self.command_result_parser.set_command_result(result=test_result, unpicklable=unpicklable)

        # Verify
        self.assertIsInstance(result, str)
        jsonpickle.encode.assert_called_once_with(test_result, unpicklable=unpicklable)
