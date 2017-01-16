from msrest.exceptions import AuthenticationError
from msrestazure.azure_exceptions import CloudError

from cloudshell.shell.core.driver_context import AutoLoadDetails

from cloudshell.cp.azure.common.azure_clients import AzureClientsManager
from cloudshell.cp.azure.common.exceptions.autoload_exception import AutoloadException


class AutoloadOperation(object):
    def __init__(self, vm_service, network_service):
        """

        :param vm_service: cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService instance
        :param network_service: cloudshell.cp.azure.domain.services.network_service.NetworkService instance
        :return:
        """
        self.vm_service = vm_service
        self.network_service = network_service

    def _validate_api_credentials(self, cloud_provider_model, logger):
        """Verify Azure API Credentials and return AzureClientsManager instance

        :param cloud_provider_model: cloudshell.cp.azure.models.AzureCloudProviderResourceModel instance
        :param logger: logging.Logger instance
        :return: cloudshell.cp.azure.common.azure_clients.AzureClientsManager instance
        """
        try:
            return AzureClientsManager(cloud_provider_model)
        except AuthenticationError:
            error_msg = "Failed to connect to Azure API, please check the log for more details"

            logger.exception(error_msg)
            raise AutoloadException(error_msg)

    def _validate_mgmt_resource_group(self, resource_client, mgmt_group_name, region, logger):
        """Verify that "Management Group Name" exists

        :param resource_client: azure.mgmt.resource.ResourceManagementClient instance
        :param mgmt_group_name: (str) management resource group name
        :param region: (str) azure region
        :param logger: logging.Logger instance
        :return:
        """
        try:
            resource_group = self.vm_service.get_resource_group(resource_management_client=resource_client,
                                                                group_name=mgmt_group_name)
        except CloudError:
            error_msg = "Failed to find Management group {}".format(mgmt_group_name)

            logger.exception(error_msg)
            raise AutoloadException(error_msg)
        else:
            if region != resource_group.location:
                error_msg = "Management group {} is not under the {} region".format(
                    mgmt_group_name,
                    region)

                raise AutoloadException(error_msg)

    def _validate_vnet(self, virtual_networks, mgmt_group_name, network_tag, logger):
        """Verify that vNET with given tag is present under the MGMT resource group

        :param virtual_networks: list of azure.mgmt.network.models.virtual_network.VirtualNetwork instances
        :param mgmt_group_name: (str) management resource group name
        :param network_tag: (str) value for the network type tag sandbox/mgmt
        :param logger: logging.Logger instance
        :return: azure.mgmt.network.models.virtual_network.VirtualNetwork instance
        """
        logger.info("Retrieving vNet from resource group {} by tag {}={}".format(
            mgmt_group_name,
            self.network_service.NETWORK_TYPE_TAG_NAME,
            network_tag))

        vnet = self.network_service.get_virtual_network_by_tag(
            virtual_networks=virtual_networks,
            tag_key=self.network_service.NETWORK_TYPE_TAG_NAME,
            tag_value=network_tag)

        if vnet is None:
            error_msg = 'Failed to find Vnet with network type "{}" tag under Management group {}'.format(
                network_tag,
                mgmt_group_name)

            raise AutoloadException(error_msg)

        return vnet

    def _validate_vm_size(self, compute_client, region, vm_size):
        """Verify "VM Size" attribute is valid

        :param compute_client: azure.mgmt.compute.compute_management_client.ComputeManagementClient instance
        :param region: (str) azure region
        :param vm_size: (str) instance type for the VM
        :return:
        """
        azure_vm_sizes = self.vm_service.list_virtual_machine_sizes(compute_management_client=compute_client,
                                                                    location=region)

        if vm_size not in (azure_vm_size.name for azure_vm_size in azure_vm_sizes):
            raise AutoloadException("VM Size {} is not valid".format(vm_size))

    def _register_azure_providers(self, resource_client, logger):
        """Add registration to the azure providers

        :param resource_client: azure.mgmt.resource.ResourceManagementClient instance
        :param logger: logging.Logger instance
        :return:
        """
        for provider in ("Microsoft.Authorization",
                         "Microsoft.Storage",
                         "Microsoft.Network",
                         "Microsoft.Compute"):

            logger.info("Register subscription with a {} resource provider".format(provider))
            resource_client.providers.register(provider)

    def _validate_networks_in_use(self, sandbox_vnet, networks_in_use):
        """Verify "Networks In Use" attribute

        :param sandbox_vnet: azure.mgmt.network.models.virtual_network.VirtualNetwork instance
        :param networks_in_use: list of used networks ["10.10.10.10/24", "20.20.20.20/24", ...]
        :return:
        """
        sandbox_cidrs = set([subnet.address_prefix for subnet in sandbox_vnet.subnets])
        cidrs = sandbox_cidrs - set(networks_in_use)

        if cidrs:
            error_msg = 'The following subnets "{}" were found under the "{}" VNet in Azure and should be set ' \
                        'in the "Network In Use" field.'.format(', '.join(cidrs), sandbox_vnet.name)

            raise AutoloadException(error_msg)

    def get_inventory(self, cloud_provider_model, logger):
        """Check that all needed resources are valid and present on the Azure

        :param cloud_provider_model: cloudshell.cp.azure.models.AzureCloudProviderResourceModel instance
        :param logger: logging.Logger instance
        :return: cloudshell.shell.core.driver_context.AutoLoadDetails instance
        """
        logger.info("Starting Autoload Operation...")

        azure_clients = self._validate_api_credentials(cloud_provider_model=cloud_provider_model, logger=logger)

        self._register_azure_providers(resource_client=azure_clients.resource_client, logger=logger)

        self._validate_mgmt_resource_group(resource_client=azure_clients.resource_client,
                                           mgmt_group_name=cloud_provider_model.management_group_name,
                                           region=cloud_provider_model.region,
                                           logger=logger)

        logger.info("Retrieving virtual networks from MGMT resource group {}".format(
            cloud_provider_model.management_group_name))

        virtual_networks = self.network_service.get_virtual_networks(
            network_client=azure_clients.network_client,
            group_name=cloud_provider_model.management_group_name)

        # verify that "sandbox" vNet exists under the MGMT resource group
        sandbox_vnet = self._validate_vnet(virtual_networks=virtual_networks,
                                           mgmt_group_name=cloud_provider_model.management_group_name,
                                           network_tag=self.network_service.SANDBOX_NETWORK_TAG_VALUE,
                                           logger=logger)

        # verify that "mgmt" vNet exists under the MGMT resource group
        self._validate_vnet(virtual_networks=virtual_networks,
                            mgmt_group_name=cloud_provider_model.management_group_name,
                            network_tag=self.network_service.MGMT_NETWORK_TAG_VALUE,
                            logger=logger)

        if cloud_provider_model.vm_size:
            self._validate_vm_size(compute_client=azure_clients.compute_client,
                                   region=cloud_provider_model.region,
                                   vm_size=cloud_provider_model.vm_size)

        self._validate_networks_in_use(sandbox_vnet=sandbox_vnet,
                                       networks_in_use=cloud_provider_model.networks_in_use)

        logger.info("Autoload Operation was successfully completed")

        return AutoLoadDetails([], [])
