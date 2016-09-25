class AzureClientFactory(object):
    def __init__(self, client_handlers, service_principal_credentials, subscription_id):
        """

        :param [HandlerBase] client_handlers:
        :param service_principal_credentials:
        :param subscription_id:
        :return:
        """
        self.service_principal_credentials = service_principal_credentials
        self.subscription_id = subscription_id
        self.clients_handlers = client_handlers

    def register_handler(self, handler):
        self.clients_handlers.append(handler)

    def get_client(self, client_type):
        return next(handler.get_client(self.service_principal_credentials, self.subscription_id) for handler in
                    self.clients_handlers if handler.can_handle(client_type=client_type))


