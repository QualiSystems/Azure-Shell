import time


class TaskWaiterService(object):

    def __init__(self, cancellation_service):
        """

        :param cancellation_service: cloudshell.cp.azure.domain.services.command_cancellation.CommandCancellationService
        """
        self.cancellation_service = cancellation_service

    def wait_for_task(self, operation_poller, cancellation_context, wait_time=30):
        """Wait for Azure operation end

        :param operation_poller: msrestazure.azure_operation.AzureOperationPoller instance
        :param cancellation_context:
        :param wait_time: (int) seconds to wait before polling request
        :return:
        """
        while not operation_poller.done():
            self.cancellation_service.check_if_cancelled(cancellation_context)
            time.sleep(wait_time)

        return operation_poller.result()
