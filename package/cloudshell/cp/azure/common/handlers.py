from cloudshell.cp.azure.domain.context.client_contextes import ComputeManagementClientContext, \
    ResourceManagementClientContext, NetworkManagementClientContext, StorageManagementClientContext


class HandlerBase(object):
    def __init__(self, handler_type):
        self.handler_type = handler_type

    def can_handle(self, client_type):
        return client_type == self.handler_type

    def get_client(self, service_principal_credentials, subscription_id):
        pass


class ComputeManagementClientHandler(HandlerBase):
    def __init__(self, handler_type):
        super(ComputeManagementClientHandler, self).__init__(handler_type)

    def get_client(self, service_principal_credentials, subscription_id):
        with ComputeManagementClientContext(service_principal_credentials=service_principal_credentials,
                                            subscription_id=subscription_id) as client:
            return client


class ResourceManagementClientHandler(HandlerBase):
    def __init__(self, handler_type):
        super(ResourceManagementClientHandler, self).__init__(handler_type)

    def get_client(self, service_principal_credentials, subscription_id):
        with ResourceManagementClientContext(service_principal_credentials=service_principal_credentials,
                                             subscription_id=subscription_id) as client:
            return client


class NetworkManagementClientHandler(HandlerBase):
    def __init__(self, handler_type):
        super(NetworkManagementClientHandler, self).__init__(handler_type)

    def get_client(self, service_principal_credentials, subscription_id):
        with NetworkManagementClientContext(service_principal_credentials=service_principal_credentials,
                                            subscription_id=subscription_id) as client:
            return client


class StorageManagementClientHandler(HandlerBase):
    def __init__(self, handler_type):
        super(StorageManagementClientHandler, self).__init__(handler_type)

    def get_client(self, service_principal_credentials, subscription_id):
        with StorageManagementClientContext(service_principal_credentials=service_principal_credentials,
                                            subscription_id=subscription_id) as client:
            return client
