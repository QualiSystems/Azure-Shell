import jsonpickle
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from converters.resource_context_converter import ResourceContextConverter
from helpers.deployment_helper import DeploymentHelper
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface


class DeployAzureVM(ResourceDriverInterface):

    def __init__(self):

        self.deployment_helper = DeploymentHelper()
        self.resource_context_converter = ResourceContextConverter()

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    def Deploy(self, context, Name=None):
        with LoggingSessionContext(context) as logger:
            with CloudShellSessionContext(context) as session:
                logger.info('Deploy started')

                # create deployment resource model and serialize it to json
                azure_vm_deployment_model = self.resource_context_converter\
                    .resource_context_to_deployment_resource_model(context.resource, '')

                vm_res_name = jsonpickle.decode(context.resource.app_context.app_request_json)['name']

                deployment_info = self.deployment_helper.get_deployment_info(azure_vm_deployment_model, vm_res_name)

                # Calls command on the Azure Cloud Provider
                result = session.ExecuteCommand(context.reservation.reservation_id,
                                                azure_vm_deployment_model.cloud_provider,
                                                "Resource",
                                                "deploy_vm",
                                                self.deployment_helper.get_command_inputs_list(deployment_info),
                                                False)
                return result.Output
