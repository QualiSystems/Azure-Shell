from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials

from cloudshell.cp.azure.common.azure_client_factory import AzureClientFactory
from cloudshell.cp.azure.common.handlers import ComputeManagementClientHandler, ResourceManagementClientHandler, \
    NetworkManagementClientHandler, StorageManagementClientHandler


class AzureClientFactoryContext(object):
    """
    This context returns a factory of all the azure clients
    """

    def __init__(self, cloud_provider_model):
        """

        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:
        :return:
        """
        self.subscription_id = self.get_subscription(cloud_provider_model)
        self.service_principal_credentials = self.get_credentials(cloud_provider_model)
        self.azure_client_handlers = [StorageManagementClientHandler(StorageManagementClient),
                                      ComputeManagementClientHandler(ComputeManagementClient),
                                      ResourceManagementClientHandler(ResourceManagementClient),
                                      NetworkManagementClientHandler(NetworkManagementClient)]

    @staticmethod
    def get_credentials(cloud_provider_model):
        """

        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:
        :return:
        """

        return ServicePrincipalCredentials(client_id=cloud_provider_model.azure_client_id,
                                           secret=cloud_provider_model.azure_secret,
                                           tenant=cloud_provider_model.azure_tenant)

    @staticmethod
    def get_subscription(cloud_provider_model):
        """

        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:
        :return:
        """
        return cloud_provider_model.azure_subscription_id

    def __enter__(self):
        return AzureClientFactory(client_handlers=self.azure_client_handlers,
                                  service_principal_credentials=self.service_principal_credentials,
                                  subscription_id=self.subscription_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
