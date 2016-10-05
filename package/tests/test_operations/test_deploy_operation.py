from unittest import TestCase

from mock import Mock
from mock import MagicMock
import mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import DeployAzureVMOperation
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_model import DeployAzureVMResourceModel


class TestDeployAzureVMOperation(TestCase):
    def setUp(self):
        self.logger = Mock()
        self.storage_service = StorageService()
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.tag_service = TagService()
        self.vm_credentials_service = Mock()
        self.deploy_operation = DeployAzureVMOperation(logger=self.logger,
                                                       vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       storage_service=self.storage_service,
                                                       vm_credentials_service=self.vm_credentials_service,
                                                       tags_service=self.tag_service)

    def test_deploy_operation_deploy_result(self):
        """
        This method verifies the basic deployment of vm.
        :return:
        """

        # Arrange
        self.vm_service.create_resource_group = Mock(return_value=True)
        self.storage_service.create_storage_account = Mock(return_value=True)
        self.network_service.create_network = MagicMock()
        self.vm_service.create_vm = MagicMock()
        self.deploy_operation._get_image_operation_system = Mock()

        # Act
        self.deploy_operation.deploy(DeployAzureVMResourceModel(),
                                     AzureCloudProviderResourceModel(),
                                     Mock(),
                                     Mock(),
                                     Mock(),
                                     Mock(),
                                     Mock())

        # Verify
        self.vm_service.create_resource_group.assert_called_once()
        self.storage_service.create_storage_account.assert_called_once()
        self.network_service.create_network.assert_called_once()
        self.vm_service.create_vm.assert_called_once()

    def test_get_image_operation_system(self):
        """Check that method returns operating_system of the provided image"""
        cloud_provider_model = mock.MagicMock()
        azure_vm_deployment_model = mock.MagicMock()
        compute_client = mock.MagicMock()
        image = mock.MagicMock()
        compute_client.virtual_machine_images.get.return_value = image

        os_type = self.deploy_operation._get_image_operation_system(
            cloud_provider_model=cloud_provider_model,
            azure_vm_deployment_model=azure_vm_deployment_model,
            compute_client=compute_client)

        compute_client.virtual_machine_images.list.assert_called_once()
        compute_client.virtual_machine_images.get.assert_called_once()
        self.assertEqual(os_type, image.os_disk_image.operating_system)
