from retrying import retry

import cloudshell.cp.azure.common.helpers.retrying_helpers as retrying_helpers
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import RouteTableRequestResourceModel


class AddRouteOperation(object):
    def __init__(self,network_service):
        """
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:

        """
        self.network_service= network_service

    @retry(stop_max_attempt_number=retrying_helpers.retryable_error_max_attempts,
           wait_fixed=retrying_helpers.retryable_wait_time,
           retry_on_exception=retrying_helpers.retry_if_retryable_error)
    def create_route_table(self,
                           route_table_request,
                           cloud_provider_model,
                           network_client,
                           sandbox_id,
                           subnet_lcoker):

        """
        :param RouteTableRequestResourceModel route_table_request:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param network_client:
        :param resource_group:
        :param subnets:
        :return:
        """
        sandbox_vnet = self.network_service.get_sandbox_virtual_network(network_client,
                                                                        cloud_provider_model.management_group_name).name

        self.network_service.create_route_table(network_client,
                                                cloud_provider_model,
                                                route_table_request,
                                                sandbox_id)
        with subnet_lcoker:

            self.network_service.add_route_table_to_subnets(sandbox_id,
                                                            route_table_request.name,
                                                            network_client,
                                                            route_table_request.subnets,
                                                            cloud_provider_model.management_group_name,
                                                            sandbox_vnet)
