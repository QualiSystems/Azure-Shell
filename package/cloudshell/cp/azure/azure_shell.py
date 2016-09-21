from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.cp.azure.domain.context.azure_client_context import AzureClientFactoryContext
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.parsers.azure_model_parser import AzureModelsParser
from cloudshell.cp.azure.domain.services.parsers.command_result_parser import CommandResultsParser
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import DeployAzureVMOperation


class AzureShell(object):
    def __init__(self):
        self.command_result_parser = CommandResultsParser()
        self.model_parser = AzureModelsParser()

    def deploy_azure_vm(self, command_context, deployment_request):
        """
        Will deploy Azure Image on the cloud provider
        :param ResourceCommandContext command_context:
        :param JSON Obj deployment_request:
        """

        cloud_provider_model = self.model_parser.convert_to_cloud_provider_resource_model(command_context.resource)
        azure_vm_deployment_model = self.model_parser.convert_to_deployment_resource_model(deployment_request)

        with AzureClientFactoryContext(command_context) as azure_clients_factory:
            with LoggingSessionContext(command_context) as logger:
                with ErrorHandlingContext(logger):
                    logger.info('Deploying Azure VM')

                    compute_client = azure_clients_factory.get_client(ComputeManagementClient)
                    resource_client = azure_clients_factory.get_client(ResourceManagementClient)
                    network_client = azure_clients_factory.get_client(NetworkManagementClient)
                    storage_client = azure_clients_factory.get_client(StorageManagementClient)

                    vm_service = VirtualMachineService(compute_management_client=compute_client,
                                                       resource_management_client=resource_client)

                    network_service = NetworkService(network_client=network_client)

                    storage_service = StorageService(storage_client=storage_client)

                    tags_service = TagService()

                    deploy_azure_vm_operation = DeployAzureVMOperation(logger=logger,
                                                                       vm_service=vm_service,
                                                                       network_service=network_service,
                                                                       storage_service=storage_service,
                                                                       tags_service=tags_service)

                    deploy_data = deploy_azure_vm_operation.deploy(azure_vm_deployment_model=azure_vm_deployment_model,
                                                                   cloud_provider_model=cloud_provider_model,
                                                                   reservation_id=command_context.reservation.reservation_id)

                    # ---Remove this----
                    # deploy_data = None
                    # ------------------

                    return self.command_result_parser.set_command_result(deploy_data)
