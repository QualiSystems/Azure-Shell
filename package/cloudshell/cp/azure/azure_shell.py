from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.cp.azure.domain.context.azure_shell import AzureShellContext
from cloudshell.cp.azure.domain.services.parsers.azure_model_parser import AzureModelsParser
from cloudshell.cp.azure.domain.services.parsers.command_result_parser import CommandResultsParser
from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import DeployAzureVMOperation


class AzureShell(object):
    def __init__(self):
        self.command_result_parser = CommandResultsParser()
        self.model_parser = AzureModelsParser()

        self.deploy_azure_vm_operation = DeployAzureVMOperation()

    def deploy_azure_vm(self, command_context, deployment_request):
        """
        Will deploy Azure Image on the cloud provider
        :param ResourceCommandContext command_context:
        :param JSON Obj deployment_request:
        """

        with AzureShellContext() as shell_context:
            with ErrorHandlingContext(shell_context.logger):
                shell_context.logger.info('Deploying Azure VM')

                azure_vm_deployment_model = self.model_parser.convert_to_deployment_resource_model(deployment_request)

                deploy_data = self.deploy_azure_vm_operation \
                    .deploy(logger=shell_context.logger,
                            compute_client=shell_context.compute_client,
                            azure_vm_deployment_model=azure_vm_deployment_model)

                return self.command_result_parser.set_command_result(deploy_data)
