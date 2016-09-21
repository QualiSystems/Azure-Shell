from unittest import TestCase
import uuid
from mock import Mock
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import DeployAzureVMOperation
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_model import DeployAzureVMResourceModel
from tests.test_helpers.test_helper import TestHelper


class TestAzureShell(TestCase):
    def setUp(self):
        self.logger = Mock()
        self.storage_service = StorageService(Mock())
        self.vm_service = VirtualMachineService(Mock(), Mock())
        self.network_service = NetworkService(Mock())
        self.tag_service = TagService()
        self.deploy_operation = DeployAzureVMOperation(logger=self.logger,
                                                       vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       storage_service=self.storage_service,
                                                       tags_service=self.tag_service)

    def test_deploy_operation_deploy_result(self):
        """
        This method verifies the basic deployment of vm.
        :return:
        """

        # Arrange
        self.vm_service.create_resource_group = Mock(return_value=True)
        self.storage_service.create_storage_account = Mock(return_value=True)
        self.network_service.create_network = Mock(return_value="The Created NIC")
        self.vm_service.create_vm = Mock(return_value=Mock())

        # Act
        self.deploy_operation.deploy(DeployAzureVMResourceModel(), AzureCloudProviderResourceModel(), Mock())

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.create_resource_group))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.storage_service.create_storage_account))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.network_service.create_network))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.create_vm))
