from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import \
    DeployAzureVMFromCustomImageResourceModel, BaseDeployAzureVMResourceModel, DeployAzureVMResourceModel
from cloudshell.cp.azure.models.image_data import ImageDataModel


class ImageDataFactory(object):
    def __init__(self, vm_service):
        """
        :param VirtualMachineService vm_service:
        :return:
        """
        self.vm_service = vm_service

    def get_image_data_model(self, cloud_provider_model, deployment_model, compute_client, logger):
        """
        :param BaseDeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param logging.Logger logger:
        :return:
        :rtype: ImageDataModel
        """
        if isinstance(deployment_model, DeployAzureVMFromCustomImageResourceModel):
            return self._get_custom_image_data(deployment_model=deployment_model, logger=logger)

        elif isinstance(deployment_model, DeployAzureVMResourceModel):
            return self._get_marketplace_image_data(deployment_model=deployment_model,
                                                    cloud_provider_model=cloud_provider_model,
                                                    compute_client=compute_client,
                                                    logger=logger)

        raise Exception("Unsupported deployment_model type")

    def _get_custom_image_data(self, deployment_model, logger):
        """
        :param DeployAzureVMFromCustomImageResourceModel deployment_model:
        :param logging.Logger logger:
        :return:
        :rtype: ImageDataModel
        """
        # Image data for custom image is redundant with managed disks
        return ImageDataModel(None, None)

    def _get_marketplace_image_data(self, deployment_model, cloud_provider_model, compute_client, logger):
        """
        :param DeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param logging.Logger logger:
        :return:
        :rtype: ImageDataModel
        """
        logger.info("Retrieving operation system type for the VM Image {}:{}:{}".format(
                deployment_model.image_publisher,
                deployment_model.image_offer,
                deployment_model.image_sku))

        virtual_machine_image = self.vm_service.get_virtual_machine_image(
                compute_management_client=compute_client,
                location=cloud_provider_model.region,
                publisher_name=deployment_model.image_publisher,
                offer=deployment_model.image_offer,
                skus=deployment_model.image_sku)

        os_type = virtual_machine_image.os_disk_image.operating_system

        logger.info("Operation system type for the VM is {}".format(os_type))

        return ImageDataModel(os_type, virtual_machine_image.plan)

