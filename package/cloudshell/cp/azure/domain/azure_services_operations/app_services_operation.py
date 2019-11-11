import logging

from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import SiteConfig, Site, AppServicePlan, SkuDescription
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.cp.core.models import ConnectSubnet
from cloudshell.shell.core.driver_context import CancellationContext
from typing import List

from cloudshell.cp.azure.domain.services.command_cancellation import CommandCancellationService
from cloudshell.cp.azure.domain.services.name_provider import NameProviderService
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureAppServiceResourceModel
from cloudshell.cp.azure.models.reservation_model import ReservationModel


class AppServicesOperation(object):
    def __init__(self, network_service, tags_service, name_provider_service, cancellation_service):
        """
        :param NetworkService network_service:
        :param TagService tags_service:
        :param NameProviderService name_provider_service:
        :param CommandCancellationService cancellation_service:
        """
        self.network_service = network_service
        self.tags_service = tags_service
        self.name_provider_service = name_provider_service
        self.cancellation_service = cancellation_service

    def deploy_code(self, deployment_model, cloud_provider_model, reservation, website_client, network_client,
                    network_actions,
                    cancellation_context, logger, cloudshell_session):
        """
        Deploy an app service web app from code
        :param WebSiteManagementClient website_client:
        :param DeployAzureAppServiceResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param ReservationModel reservation:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param List[ConnectSubnet] network_actions:
        :param CancellationContext cancellation_context:
        :param logging.Logger logger:
        :param CloudShellAPISession cloudshell_session:
        :return:
        """

        resource_group_name = reservation.reservation_id

        resource_postfix = self.name_provider_service.generate_short_unique_string()
        web_app_name = self.name_provider_service.generate_name(deployment_model.app_name,
                                                                resource_postfix,
                                                                max_length=24)
        app_service_plan_name = 'ASP-{}'.format(web_app_name)

        # create an app service plan
        create_app_service_plan_operation = website_client.app_service_plans.create_or_update(
            resource_group_name,
            app_service_plan_name,
            AppServicePlan(cloud_provider_model.region,
                           # tags=self.tags_service.get_tags(app_service_plan_name, reservation),
                           # kind='app',
                           app_service_plan_name,
                           sku=SkuDescription(name='S1',
                                              tier='Standard',
                                              size='S1',
                                              family='S',
                                              capacity=1
                                              )
                           )
        )
        create_app_service_plan_operation.wait()
        app_service_plan = create_app_service_plan_operation.result()

        # create a web app
        site_configuration = SiteConfig(
            node_version='10.14'
        )
        create_web_app_operation = website_client.web_apps.create_or_update(
            resource_group_name,
            web_app_name,
            Site(
                location=cloud_provider_model.region,
                server_farm_id=app_service_plan.id,
                site_config=site_configuration,
                tags=self.tags_service.get_tags(web_app_name, reservation)
            )
        )

        result = create_web_app_operation.result()
