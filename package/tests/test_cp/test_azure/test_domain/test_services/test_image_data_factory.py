from unittest import TestCase

from mock import Mock, MagicMock

from cloudshell.cp.azure.domain.services.image_data import ImageDataFactory
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMFromCustomImageResourceModel, \
    DeployAzureVMResourceModel


class TestImageDataFactory(TestCase):
    def setUp(self):
        self.vm_service = Mock()
        self.image_data_factory = ImageDataFactory(vm_service=self.vm_service)
        self.logger = Mock()
        self.compute_client = Mock()
        self.cloud_provider_model = Mock()

    def test_unsupported_deployment_model(self):
        deployment_model = Mock()

        with self.assertRaisesRegexp(Exception, "Unsupported deployment_model type"):
            self.image_data_factory.get_image_data_model(deployment_model=deployment_model,
                                                         cloud_provider_model=self.cloud_provider_model,
                                                         compute_client=self.compute_client,
                                                         logger=self.logger)

    def test_get_image_data_model_for_custom_image(self):
        # arrange
        deployment_model = DeployAzureVMFromCustomImageResourceModel()
        expected_result = Mock()
        self.image_data_factory._get_custom_image_data = Mock(return_value=expected_result)
        self.image_data_factory._get_marketplace_image_data = Mock()

        # act
        result = self.image_data_factory.get_image_data_model(deployment_model=deployment_model,
                                                              cloud_provider_model=self.cloud_provider_model,
                                                              compute_client=self.compute_client,
                                                              logger=self.logger)

        self.assertEquals(result, expected_result)
        self.image_data_factory._get_custom_image_data.assert_called_once_with(
                deployment_model=deployment_model, compute_client=self.compute_client, logger=self.logger)
        self.image_data_factory._get_marketplace_image_data.assert_not_called()

    def test_get_image_data_model_for_marketplace_image(self):
        # arrange
        deployment_model = DeployAzureVMResourceModel()
        expected_result = Mock()
        self.image_data_factory._get_custom_image_data = Mock()
        self.image_data_factory._get_marketplace_image_data = Mock(return_value=expected_result)

        # act
        result = self.image_data_factory.get_image_data_model(deployment_model=deployment_model,
                                                              cloud_provider_model=self.cloud_provider_model,
                                                              compute_client=self.compute_client,
                                                              logger=self.logger)

        self.assertEquals(result, expected_result)
        self.image_data_factory._get_marketplace_image_data.assert_called_once_with(
                deployment_model=deployment_model,
                logger=self.logger,
                cloud_provider_model=self.cloud_provider_model,
                compute_client=self.compute_client)
        self.image_data_factory._get_custom_image_data.assert_not_called()

    def test_get_custom_image_data(self):
        # arrange
        deployment_model = Mock()
        image_mock = Mock()
        self.compute_client.images.get = Mock(return_value=image_mock)

        # act
        result = self.image_data_factory._get_custom_image_data(deployment_model=deployment_model,
                                                                compute_client=self.compute_client,
                                                                logger=self.logger)

        # assert
        self.assertEquals(result.os_type, image_mock.storage_profile.os_disk.os_type)
        self.assertEquals(result.image_id, image_mock.id)

    def test_get_marketplace_image_data(self):
        # arrange
        deployment_model = Mock()
        image = MagicMock()
        self.vm_service.get_virtual_machine_image = Mock(return_value=image)

        # act
        result = self.image_data_factory._get_marketplace_image_data(deployment_model=deployment_model,
                                                                     logger=self.logger,
                                                                     cloud_provider_model=self.cloud_provider_model,
                                                                     compute_client=self.compute_client)

        # assert
        self.vm_service.get_virtual_machine_image.assert_called_once_with(
                compute_management_client=self.compute_client,
                location=self.cloud_provider_model.region,
                publisher_name=deployment_model.image_publisher,
                offer=deployment_model.image_offer,
                skus=deployment_model.image_sku)
        self.assertEquals(result.os_type, image.os_disk_image.operating_system)
        self.assertEquals(result.purchase_plan, image.plan)
