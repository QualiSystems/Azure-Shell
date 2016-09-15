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
        azure_resource_model.azure_client_id = resource_context['Azure Client ID']
        azure_resource_model.azure_mgmt_network_d = resource_context['Azure Mgmt Network ID']
        azure_resource_model.azure_mgmt_nsg_id = resource_context['Azure Mgmt NSG ID']
        azure_resource_model.azure_mgmt_vnet = resource_context['Azure Mgmt VNET']
        azure_resource_model.azure_secret = resource_context['Azure Secret']
        azure_resource_model.azure_subscription_id = resource_context['Azure Subscription ID']
        azure_resource_model.azure_tenant = resource_context['Azure Tenant']
        azure_resource_model.instance_type = resource_context['Instance Type']
        azure_resource_model.keypairs_location = resource_context['Keypairs Location']
        azure_resource_model.networks_in_use = resource_context['Networks In Use']
        azure_resource_model.region = resource_context['Region']
        azure_resource_model.storage_type = resource_context['Storage Type']

        return azure_resource_model





