from cloudshell.cp.azure.models.deploy_result_model import DeployResult


class DeployAzureVMOperation(object):
    """

    """

    def __init__(self):
        """

        """

    def deploy(self, logger, compute_client, azure_vm_deployment_model):
        """

        :param azure_vm_deployment_model:
        :param compute_client:
        :param logging.Logger logger:
        :return: DeployResult result
        """

        deploy_data = compute_client.virtual_machines.create_or_update(
            azure_vm_deployment_model.group_name,
            azure_vm_deployment_model.vm_name
        )

        return DeployResult()
