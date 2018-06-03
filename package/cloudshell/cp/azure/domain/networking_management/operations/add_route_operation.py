class AddRouteOperation(object):
    def __init__(self,network_service):
        """
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:

        """
        self.network_service= network_service

    def create_route_table(self, route_table_request, cloud_provider_model, network_client, resource_group):
        self.network_service.create_route_table(network_client,cloud_provider_model,route_table_request,resource_group)

