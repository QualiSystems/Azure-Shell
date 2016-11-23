import jsonpickle

from cloudshell.core.context.error_handling_context import ErrorHandlingContext
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.cp.azure.common.converters.resource_context import ResourceContextConverter
from cloudshell.cp.azure.common.helpers.deployment_helper import DeploymentHelper


class DeployAzureVMFromCustomImage(ResourceDriverInterface):

    def __init__(self):
        self.deployment_helper = DeploymentHelper()
        self.resource_context_converter = ResourceContextConverter()

    def cleanup(self):
        pass

    def initialize(self, context):
        pass

    def Deploy(self, context, Name=None):
        with LoggingSessionContext(context) as logger:
            with ErrorHandlingContext(logger):
                with CloudShellSessionContext(context) as session:
                    logger.info('Deploy started')

                    # create deployment resource model and serialize it to json
                    azure_vm_from_custom_image_mode = (
                        self.resource_context_converter.resource_context_to_deploy_azure_vm_from_custom_image_model(
                            context.resource, ''))

                    app_request = jsonpickle.decode(context.resource.app_context.app_request_json)

                    vm_res_name = app_request['name']
                    cloud_provider_name = app_request["deploymentService"].get("cloudProviderName")

                    if cloud_provider_name:
                        azure_vm_from_custom_image_mode.cloud_provider = str(cloud_provider_name)

                    deployment_info = self.deployment_helper.get_deployment_info(
                        azure_vm_from_custom_image_mode,
                        vm_res_name)

                    # Calls command on the Azure Cloud Provider
                    result = session.ExecuteCommand(context.reservation.reservation_id,
                                                    azure_vm_from_custom_image_mode.cloud_provider,
                                                    "Resource",
                                                    "deploy_vm_from_custom_image",
                                                    self.deployment_helper.get_command_inputs_list(deployment_info),
                                                    False)
                    return result.Output
