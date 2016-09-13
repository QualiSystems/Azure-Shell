import jsonpickle
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel

from cloudshell.cp.azure.models.deploy_azure_vm_resource_model import DeployAzureVMResourceModel
from cloudshell.cp.azure.common.deploy_data_holder import DeployDataHolder

class AzureModelsParser(object):
    @staticmethod
    def convert_to_deployment_resource_model(deployment_request):
        data = jsonpickle.decode(deployment_request)
        data_holder = DeployDataHolder(data)
        deployment_resource_model = DeployAzureVMResourceModel()
        deployment_resource_model.group_name = data_holder.ami_params.group_name
        deployment_resource_model.vm_name = data_holder.ami_params.vm_name
        deployment_resource_model.cloud_provider = data_holder.ami_params.cloud_provider

        # todo

        return deployment_resource_model

    @staticmethod
    def convert_to_cloud_provider_resource_model(resource):
        """
        :param resource:
        :return: AzureCloudProviderResourceModel
        """
        resource_context = resource.attributes
        azure_resource_model = AzureCloudProviderResourceModel()
        # todo


        return azure_resource_model