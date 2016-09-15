from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient


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