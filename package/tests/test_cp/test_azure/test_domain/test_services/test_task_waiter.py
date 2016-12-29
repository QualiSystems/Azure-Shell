from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.services.task_waiter import TaskWaiterService


class TestTaskWaiterService(TestCase):
    def setUp(self):
        self.cancellation_service = mock.MagicMock()
        self.task_waiter_service = TaskWaiterService(cancellation_service=self.cancellation_service)

    @mock.patch("cloudshell.cp.azure.domain.services.task_waiter.time.sleep")
    def test_wait_for_task(self, sleep):
        """Check that method will return azure poller result once operation will end"""
        operation_poller = mock.MagicMock()
        cancellation_context = mock.MagicMock()
        operation_poller.done.side_effect = [False, True]

        # Act
        result = self.task_waiter_service.wait_for_task(operation_poller=operation_poller,
                                                        cancellation_context=cancellation_context)
        # Verify
        self.assertEqual(result, operation_poller.result())
        operation_poller.done.assert_called()
        sleep.assert_called_once_with(30)
        self.cancellation_service.check_if_cancelled.assert_called_once_with(cancellation_context)
