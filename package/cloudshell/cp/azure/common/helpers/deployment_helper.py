import jsonpickle

from cloudshell.api.cloudshell_api import InputNameValue, CommandExecutionCancelledResultInfo
from cloudshell.cp.azure.common.deploy_data_holder import DeployDataHolder


class DeploymentHelper(object):

    def get_deployment_info(self, image_model, name):
        return DeployDataHolder({'app_name': name, 'ami_params': image_model})

    def get_command_inputs_list(self, data_holder):
        return [InputNameValue('request', jsonpickle.encode(data_holder, unpicklable=False))]

    def process_command_execution_result(self, logger, result):
        if isinstance(result, CommandExecutionCancelledResultInfo):
            logger.info("Command cancelled: {}".format(result.Message))
            return result.Message
        else:
            return result.Output