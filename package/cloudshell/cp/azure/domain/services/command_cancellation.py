from cloudshell.cp.azure.common.exceptions.cancellation_exception import CancellationException


class CommandCancellationService(object):

    def check_if_cancelled(self, cancellation_context):
        """Check if command was cancelled from the CloudShell

        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :raises cloudshell.cp.azure.common.exceptions.cancellation_exception.CancellationException
        :return:
        """
        if cancellation_context.is_cancelled:
            raise CancellationException("Command was cancelled")
