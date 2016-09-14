from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient

from cloudshell.cp.azure.common.azure_client_factory import StorageManagementClientHandler, \
    ComputeManagementClientHandler, ResourceManagementClientHandler, NetworkManagementClientHandler, AzureClientFactory


class AzureClientFactoryContext(object):
    """
    This context returns a factory of all the azure clients
    """

    def __init__(self, cloud_provider_model):
        self.subscription_id = self.get_subscription(cloud_provider_model)
        self.service_principal_credentials = self.get_credentials(cloud_provider_model)
        self.azure_client_handlers = [StorageManagementClientHandler(StorageManagementClient),
                                      ComputeManagementClientHandler(ComputeManagementClient),
                                      ResourceManagementClientHandler(ResourceManagementClient),
                                      NetworkManagementClientHandler(NetworkManagementClient)]


    @staticmethod
    def get_credentials(cloud_provider_model):
        raise Exception("get_credentials not implemented")

    @staticmethod
    def get_subscription(cloud_provider_model):
        raise Exception("get_subscription not implemented")

    def __enter__(self):
        return AzureClientFactory(client_handlers=self.azure_client_handlers,
                                  service_principal_credentials=self.service_principal_credentials,
                                  subscription_id=self.subscription_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ComputeManagementClientContext(object):
    def __init__(self, service_principal_credentials, subscription_id):
        self.subscription_id = subscription_id
        self.service_principal_credentials = service_principal_credentials

    def __enter__(self):
        return ComputeManagementClient(self.service_principal_credentials, self.subscription_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ResourceManagementClientContext(object):
    def __init__(self, service_principal_credentials, subscription_id):
        self.subscription_id = subscription_id
        self.service_principal_credentials = service_principal_credentials

    def __enter__(self):
        return ResourceManagementClient(self.service_principal_credentials, self.subscription_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class NetworkManagementClientContext(object):
    def __init__(self, service_principal_credentials, subscription_id):
        self.service_principal_credentials = service_principal_credentials
        self.subscription_id = subscription_id

    def __enter__(self):
        return NetworkManagementClient(self.service_principal_credentials, self.subscription_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class StorageManagementClientContext(object):
    def __init__(self, service_principal_credentials, subscription_id):
        self.service_principal_credentials = service_principal_credentials
        self.subscription_id = subscription_id

    def __enter__(self):
        return StorageManagementClient(self.service_principal_credentials, self.subscription_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
