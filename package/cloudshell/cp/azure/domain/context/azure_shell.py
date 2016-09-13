import azure
from azure.mgmt.compute import ComputeManagementClient
from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext


class AzureShellContext(object):
    def __init__(self):
        """

        """

    def __enter__(self):
        """
        Initializes all azure shell context dependencies
        :rtype AzureShellContextModel:
        """
        with LoggingSessionContext(self.context) as logger:
            with ErrorHandlingContext(logger):
                return AzureShellContextModel(logger=logger)


class AzureShellContextModel(object):
    def __init__(self, logger):
        """
        :param logging.Logger logger:
        :return:
        """
        self.logger = logger
        self.compute_client = ComputeManagementClient(
            "TBD",
            "TBD")
