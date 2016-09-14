from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.cp.azure.common.azure_client_factory import StorageManagementClientHandler, \
    ComputeManagementClientHandler, ResourceManagementClientHandler, NetworkManagementClientHandler, AzureClientFactory
from cloudshell.cp.azure.domain.services.parsers.azure_model_parser import AzureModelsParser
from cloudshell.cp.azure.domain.services.parsers.command_result_parser import CommandResultsParser
from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import DeployAzureVMOperation


class AzureShell(object):
    def __init__(self, service_principal_credentials, subscription_id):
        self.command_result_parser = CommandResultsParser()
        self.model_parser = AzureModelsParser()
        self.azure_clients_factory = self._init_azure_client_factory(
            service_principal_credentials=service_principal_credentials,
            subscription_id=subscription_id)

    def _init_azure_client_factory(self, service_principal_credentials, subscription_id):
        handlers = [StorageManagementClientHandler(StorageManagementClient),
                    ComputeManagementClientHandler(ComputeManagementClient),
                    ResourceManagementClientHandler(ResourceManagementClient),
                    NetworkManagementClientHandler(NetworkManagementClient)]

        return AzureClientFactory(client_handlers=handlers,
                                  service_principal_credentials=service_principal_credentials,
                                  subscription_id=subscription_id)

    def deploy_azure_vm(self, command_context, deployment_request):
        """
        Will deploy Azure Image on the cloud provider
        :param ResourceCommandContext command_context:
        :param JSON Obj deployment_request:
        """

        with LoggingSessionContext(command_context) as logger:
            with ErrorHandlingContext(logger):
                logger.info('Deploying Azure VM')

                compute_management_client = self.azure_clients_factory.get_client(ComputeManagementClient)
                resource_management_client = self.azure_clients_factory.get_client(ResourceManagementClient)
                network_client = self.azure_clients_factory.get_client(NetworkManagementClient)
                storage_client = self.azure_clients_factory.get_client(StorageManagementClient)

                deploy_azure_vm_operation = DeployAzureVMOperation(logger=logger,
                                                                   compute_management_client=compute_management_client,
                                                                   resource_management_client=resource_management_client,
                                                                   network_client=network_client,
                                                                   storage_client=storage_client)

                azure_vm_deployment_model = self.model_parser.convert_to_deployment_resource_model(deployment_request)
                deploy_data = deploy_azure_vm_operation.deploy(azure_vm_deployment_model=azure_vm_deployment_model)
                return self.command_result_parser.set_command_result(deploy_data)
