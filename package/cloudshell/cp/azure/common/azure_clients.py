from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials

from cloudshell.cp.azure.common.singletons import SingletonByArgsMeta
from cloudshell.cp.azure.common.singletons import AbstractComparableInstance


class AzureClientsManager(AbstractComparableInstance):
    __metaclass__ = SingletonByArgsMeta

    def check_params_equality(self, cloud_provider, *args, **kwargs):
        """Check if instance have the same attributes for initializing Azure session as provided in cloud_provider

        :param cloud_provider: AzureCloudProviderResourceModel instance
        :return: (bool) True/False whether attributes are same or not
        """
        subscription_id = self._get_subscription(cloud_provider)
        client_id = self._get_azure_client_id(cloud_provider)
        secret = self._get_azure_secret(cloud_provider)
        tenant = self._get_azure_tenant(cloud_provider)

        return all([
            subscription_id == self._subscription_id,
            client_id == self._client_id,
            secret == self._secret,
            tenant == self._tenant])

    def __init__(self, cloud_provider):
        """
        :param cloud_provider: AzureCloudProviderResourceModel instance
        :return
        """
        self._subscription_id = self._get_subscription(cloud_provider)
        self._client_id = self._get_azure_client_id(cloud_provider)
        self._secret = self._get_azure_secret(cloud_provider)
        self._tenant = self._get_azure_tenant(cloud_provider)
        self._service_credentials = self._get_service_credentials()
        self._compute_client = None
        self._network_client = None
        self._storage_client = None
        self._resource_client = None

    def _get_service_credentials(self):
        return ServicePrincipalCredentials(client_id=self._client_id, secret=self._secret, tenant=self._tenant)

    def _get_subscription(self, cloud_provider_model):
        return cloud_provider_model.azure_subscription_id

    def _get_azure_client_id(self, cloud_provider_model):
        return cloud_provider_model.azure_client_id

    def _get_azure_secret(self, cloud_provider_model):
        return cloud_provider_model.azure_secret

    def _get_azure_tenant(self, cloud_provider_model):
        return cloud_provider_model.azure_tenant

    @property
    def compute_client(self):
        if self._compute_client is None:
            with SingletonByArgsMeta.lock:
                if self._compute_client is None:
                    self._compute_client = ComputeManagementClient(self._service_credentials, self._subscription_id)

        return self._compute_client

    @property
    def network_client(self):
        if self._network_client is None:
            with SingletonByArgsMeta.lock:
                if self._network_client is None:
                    self._network_client = NetworkManagementClient(self._service_credentials, self._subscription_id)

        return self._network_client

    @property
    def storage_client(self):
        if self._storage_client is None:
            with SingletonByArgsMeta.lock:
                if self._storage_client is None:
                    self._storage_client = StorageManagementClient(self._service_credentials, self._subscription_id)

        return self._storage_client

    @property
    def resource_client(self):
        if self._resource_client is None:
            with SingletonByArgsMeta.lock:
                if self._resource_client is None:
                    self._resource_client = ResourceManagementClient(self._service_credentials, self._subscription_id)

        return self._resource_client
