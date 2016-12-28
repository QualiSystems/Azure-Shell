from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.services.command_cancellation import CommandCancellationService
from cloudshell.cp.azure.common.exceptions.cancellation_exception import CancellationException


class TestTaskWaiterService(TestCase):
    def setUp(self):
        self.cancellation_service = CommandCancellationService()

    def test_check_if_cancelled(self):
        """Check that method will raise CancellationException if command is cancelled"""
        cancellation_context = mock.MagicMock()

        with self.assertRaises(CancellationException):
            self.cancellation_service.check_if_cancelled(cancellation_context=cancellation_context)
