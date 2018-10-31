from datetime import datetime, timedelta
import time

from cloudshell.cp.azure.common.exceptions.quali_timeout_exception import QualiTimeoutException


class TaskWaiterService(object):
    def __init__(self, cancellation_service):
        """

        :param cancellation_service: cloudshell.cp.azure.domain.services.command_cancellation.CommandCancellationService
        """
        self.cancellation_service = cancellation_service

    def wait_for_task(self, operation_poller, cancellation_context, wait_time=30, logger=None):
        """Wait for Azure operation end

        :param operation_poller: msrestazure.azure_operation.AzureOperationPoller instance
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :param wait_time: (int) seconds to wait before polling request
        :return: Azure Operation Poller result
        """
        while not operation_poller.done():
            if logger:
                logger.info('Waiting for poller, current status is {0}'.format(operation_poller.status()))
            self.cancellation_service.check_if_cancelled(cancellation_context)
            time.sleep(wait_time)

        return operation_poller.result()

    def wait_for_task_with_timeout(self, operation_poller, cancellation_context, wait_time=30, timeout=1800,
                                   logger=None):
        """Wait for Azure operation end

        :param timeout:
        :param operation_poller: msrestazure.azure_operation.AzureOperationPoller instance
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :param wait_time: (int) seconds to wait before polling request
        :return: Azure Operation Poller result
        """

        datetime_now = datetime.now()
        next_time = datetime_now + timedelta(seconds=timeout)

        while not operation_poller.done() and (datetime_now < next_time):
            self.cancellation_service.check_if_cancelled(cancellation_context)
            if logger:
                logger.info('Waiting for poller, current status is {0}'.format(operation_poller.status()))
            time.sleep(wait_time)
            datetime_now = datetime.now()

        if not operation_poller.done() and (datetime_now > next_time):
            if logger:
                logger.warn('Had a timeout, current status in poller is: {0}'.format(operation_poller.status()))
            raise QualiTimeoutException()

        return operation_poller.result()
