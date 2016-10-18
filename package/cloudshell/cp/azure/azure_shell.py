import jsonpickle
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient

from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.cp.azure.common.deploy_data_holder import DeployDataHolder
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.cp.azure.domain.context.azure_client_context import AzureClientFactoryContext
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.parsers.azure_model_parser import AzureModelsParser
from cloudshell.cp.azure.domain.services.parsers.command_result_parser import CommandResultsParser
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import DeployAzureVMOperation
from cloudshell.cp.azure.domain.vm_management.operations.power_operation import PowerAzureVMOperation
from cloudshell.cp.azure.domain.vm_management.operations.prepare_connectivity_operation import \
    PrepareConnectivityOperation


class AzureShell(object):
    def __init__(self):
        self.command_result_parser = CommandResultsParser()
        self.model_parser = AzureModelsParser()
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.storage_service = StorageService()
        self.tags_service = TagService()

    def deploy_azure_vm(self, command_context, deployment_request):
        """
        Will deploy Azure Image on the cloud provider
        :param ResourceCommandContext command_context:
        :param JSON Obj deployment_request:
        """

        cloud_provider_model = self.model_parser.convert_to_cloud_provider_resource_model(command_context.resource)
        azure_vm_deployment_model = self.model_parser.convert_to_deployment_resource_model(deployment_request)

        with LoggingSessionContext(command_context) as logger:
            with ErrorHandlingContext(logger):
                with AzureClientFactoryContext(cloud_provider_model) as azure_clients_factory:

                    logger.info('Deploying Azure VM')
                    compute_client = azure_clients_factory.get_client(ComputeManagementClient)
                    network_client = azure_clients_factory.get_client(NetworkManagementClient)
                    storage_client = azure_clients_factory.get_client(StorageManagementClient)

                    deploy_azure_vm_operation = DeployAzureVMOperation(logger=logger,
                                                                       vm_service=self.vm_service,
                                                                       network_service=self.network_service,
                                                                       storage_service=self.storage_service,
                                                                       tags_service=self.tags_service)

                    reservation = self.model_parser.convert_to_reservation_model(command_context.reservation)

                    deploy_data = deploy_azure_vm_operation.deploy(azure_vm_deployment_model=azure_vm_deployment_model,
                                                                   cloud_provider_model=cloud_provider_model,
                                                                   reservation=reservation,
                                                                   network_client=network_client,
                                                                   compute_client=compute_client,
                                                                   storage_client=storage_client)

                    return self.command_result_parser.set_command_result(deploy_data)

    def prepare_connectivity(self, context, request):
        """

        :param context:
        :param request:
        :return:
        """
        cloud_provider_model = self.model_parser.convert_to_cloud_provider_resource_model(context.resource)
        with LoggingSessionContext(context) as logger:
            with AzureClientFactoryContext(cloud_provider_model) as azure_clients_factory:
                logger.info('Preparing Connectivity for Azure VM')

                resource_client = azure_clients_factory.get_client(ResourceManagementClient)
                network_client = azure_clients_factory.get_client(NetworkManagementClient)
                storage_client = azure_clients_factory.get_client(StorageManagementClient)

                prepare_connectivity_operation = PrepareConnectivityOperation(logger=logger, vm_service=self.vm_service,
                                                                              network_service=self.network_service,
                                                                              storage_service=self.storage_service,
                                                                              tags_service=self.tags_service)

                prepare_connectivity_request = DeployDataHolder(jsonpickle.decode(request))
                prepare_connectivity_request = getattr(prepare_connectivity_request, 'driverRequest', None)

                result = prepare_connectivity_operation.prepare_connectivity(reservation=context.reservation,
                                                                             cloud_provider_model=cloud_provider_model,
                                                                             storage_client=storage_client,
                                                                             resource_client=resource_client,
                                                                             network_client=network_client,
                                                                             logger=logger,
                                                                             request=prepare_connectivity_request)

                return self.command_result_parser.set_command_result({'driverResponse': {'actionResults': result}})

    def power_on_vm(self, command_context):
        """Power on Azure VM

        :param ResourceCommandContext command_context:
        :return:
        """
        cloud_provider_model = self.model_parser.convert_to_cloud_provider_resource_model(command_context.resource)
        reservation = self.model_parser.convert_to_reservation_model(command_context.remote_reservation)
        group_name = reservation.reservation_id

        resource = command_context.remote_endpoints[0]
        data_holder = self.model_parser.convert_app_resource_to_deployed_app(resource)
        vm_name = data_holder.name

        with LoggingSessionContext(command_context) as logger:
            with ErrorHandlingContext(logger):
                with AzureClientFactoryContext(cloud_provider_model) as azure_clients_factory:
                    logger.info('Starting power on operation on Azure VM {}'.format(vm_name))

                    compute_client = azure_clients_factory.get_client(ComputeManagementClient)
                    power_vm_operation = PowerAzureVMOperation(logger=logger, vm_service=self.vm_service)

                    power_vm_operation.power_on(compute_client=compute_client, resource_group_name=group_name,
                                                vm_name=vm_name)

                    logger.info('Azure VM {} was successfully powered on'.format(vm_name))

                    with CloudShellSessionContext(command_context) as cloudshell_session:
                        cloudshell_session.SetResourceLiveStatus(resource.fullname, "Online", "Active")

    def power_off_vm(self, command_context):
        """Power off Azure VM

        :param ResourceCommandContext command_context:
        :return:
        """
        cloud_provider_model = self.model_parser.convert_to_cloud_provider_resource_model(command_context.resource)
        reservation = self.model_parser.convert_to_reservation_model(command_context.remote_reservation)
        group_name = reservation.reservation_id

        resource = command_context.remote_endpoints[0]
        data_holder = self.model_parser.convert_app_resource_to_deployed_app(resource)
        vm_name = data_holder.name

        with LoggingSessionContext(command_context) as logger:
            with ErrorHandlingContext(logger):
                with AzureClientFactoryContext(cloud_provider_model) as azure_clients_factory:
                    logger.info('Starting power off operation on Azure VM {}'.format(vm_name))

                    compute_client = azure_clients_factory.get_client(ComputeManagementClient)
                    power_vm_operation = PowerAzureVMOperation(logger=logger, vm_service=self.vm_service)

                    power_vm_operation.power_off(compute_client=compute_client, resource_group_name=group_name,
                                                 vm_name=vm_name)

                    logger.info('Azure VM {} was successfully powered off'.format(vm_name))

                    with CloudShellSessionContext(command_context) as cloudshell_session:
                        cloudshell_session.SetResourceLiveStatus(resource.fullname, "Offline", "Powered Off")
