from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials


class AzureClientsManager(object):

    def __init__(self, cloud_provider):
        self.service_credentials = self._get_service_credentials(cloud_provider)
        self.subscription_id = self._get_subscription(cloud_provider)

    def _get_service_credentials(self, cloud_provider_model):
        return ServicePrincipalCredentials(client_id=cloud_provider_model.azure_client_id,
                                           secret=cloud_provider_model.azure_secret,
                                           tenant=cloud_provider_model.azure_tenant)

    def _get_subscription(self, cloud_provider_model):
        return cloud_provider_model.azure_subscription_id

    def get_compute_client(self):
        return ComputeManagementClient(self.service_credentials,
                                       self.subscription_id)

    def get_network_client(self):
        return NetworkManagementClient(self.service_credentials,
                                       self.subscription_id)

    def get_storage_client(self):
        return StorageManagementClient(self.service_credentials,
                                       self.subscription_id)
