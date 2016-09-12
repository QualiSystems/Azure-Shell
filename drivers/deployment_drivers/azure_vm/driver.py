import jsonpickle
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from drivers.azure_shell.converters.resource_context_converter import ResourceContextConverter


class DeployAzureVM(ResourceDriverInterface):
    def __init__(self):
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
                aws_ami_deployment_model = self.resource_context_converter\
                    .resource_context_to_deployment_resource_model(1, '')

                # ami_res_name = jsonpickle.decode(context.resource.app_context.app_request_json)['name']

                # deployment_info = self._get_deployment_info(aws_ami_deployment_model, ami_res_name)

                # self.vaidate_deployment_ami_model(aws_ami_deployment_model)

                # Calls command on the AWS cloud provider
                # result = session.ExecuteCommand(context.reservation.reservation_id,
                #                                 aws_ami_deployment_model.cloud_provider,
                #                                 "Resource",
                #                                 "deploy_ami",
                #                                 self._get_command_inputs_list(deployment_info),
                #                                 False)
                # return result.Output

                pass
