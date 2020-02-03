from logging import Logger

from azure.mgmt.network import NetworkManagementClient
from cloudshell.api.cloudshell_api import CloudShellAPISession
from msrestazure.azure_exceptions import CloudError

from cloudshell.cp.azure.domain.services.ip_service import IpService
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.name_provider import NameProviderService

from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel


class IPAddressOperation(object):
    def __init__(self, ip_service, network_service, name_provider_service):
        """
        :param IpService ip_service:
        :param NetworkService network_service:
        :param NameProviderService name_provider_service:
        """
        self.ip_service = ip_service
        self.network_service = network_service
        self.name_provider_service = name_provider_service

    def get_available_private_ip(self, logger, cloudshell_session, cloud_provider_model, network_client,
                                 reservation_id, subnet_cidr, owner):
        """
        :param Logger logger:
        :param CloudShellAPISession cloudshell_session:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param str reservation_id:
        :param str subnet_cidr:
        :param NetworkManagementClient network_client:
        :param str owner:
        :rtype: str
        """
        logger.info("Received request to get next available private ip for reservation {} in subnet {} "
                    "for owner '{}' ".format(reservation_id, subnet_cidr, owner))

        self._validate(cloud_provider_model, logger, network_client, reservation_id, subnet_cidr)

        ip_address = self.ip_service.get_next_available_ip_from_cs_pool(
            logger, cloudshell_session, reservation_id, subnet_cidr, owner)

        logger.info("Next available private IP in {res}/{subnet} for '{owner}' is {ip}"
                    .format(res=reservation_id, subnet=subnet_cidr, owner=owner, ip=ip_address))

        return ip_address

    def _validate(self, cloud_provider_model, logger, network_client, reservation_id, subnet_cidr):
        self._validate_allocation_method(cloud_provider_model)
        self._validate_subnet_exists(cloud_provider_model, logger, network_client, reservation_id, subnet_cidr)

    def _validate_subnet_exists(self, cloud_provider_model, logger, network_client, reservation_id, subnet_cidr):
        sandbox_vnet = self.network_service.get_sandbox_virtual_network(
            network_client, cloud_provider_model.management_group_name)
        subnet_name = self.name_provider_service.format_subnet_name(reservation_id, subnet_cidr)
        try:
            network_client.subnets.get(cloud_provider_model.management_group_name,
                                       sandbox_vnet.name,
                                       subnet_name)
        except CloudError as e:
            if e.response.reason == "Not Found":
                logger.exception('Requested subnet {} doesnt exist in reservation {}'.format(subnet_cidr,
                                                                                             reservation_id))
            raise

    def _validate_allocation_method(self, cloud_provider_model):
        if cloud_provider_model.private_ip_allocation_method.lower() != 'cloudshell allocation':
            raise ValueError("GetAvailablePrivateIP is supported only when the cloud provider 'Private IP "
                             "Allocation Method' attribute is set to Cloudshell Allocation. Current allocation method is "
                             "{}".format(cloud_provider_model.private_ip_allocation_method))