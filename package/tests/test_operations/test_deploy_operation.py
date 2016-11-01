from unittest import TestCase

from mock import Mock
from mock import MagicMock

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
        self.vm_credentials_service = Mock()
        self.key_pair_service = Mock()
        self.tags_service = TagService()
        self.deploy_operation = DeployAzureVMOperation(logger=self.logger,
                                                       vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       storage_service=self.storage_service,
                                                       vm_credentials_service=self.vm_credentials_service,
                                                       key_pair_service=self.key_pair_service,
                                                       tags_service=self.tags_service)

    def test_deploy_operation_deploy_result(self):
        """
        This method verifies the basic deployment of vm.
        :return:
        """

        # Arrange
        self.vm_service.create_resource_group = Mock(return_value=True)
        self.storage_service.create_storage_account = Mock(return_value=True)
        self.storage_service.get_storage_per_resource_group = MagicMock()
        self.network_service.get_virtual_networks = Mock(return_value=[MagicMock()])
        self.network_service.create_network_for_vm = MagicMock()
        self.vm_service.get_image_operation_system = MagicMock()
        self.network_service.get_public_ip = MagicMock()
        self.vm_service.create_vm = MagicMock()
        resource_model = DeployAzureVMResourceModel()
        resource_model.add_public_ip = True

        vnet = Mock()
        subnet = MagicMock()
        name = "name"
        subnet.name = name
        vnet.subnets = [subnet]
        reservation = Mock()
        reservation.reservation_id = name
        self.network_service.get_sandbox_virtual_network = Mock(return_value=vnet)

        # Act
        self.deploy_operation.deploy(resource_model,
                                     AzureCloudProviderResourceModel(),
                                     reservation,
                                     MagicMock(),
                                     Mock(),
                                     Mock(),
                                     Mock())

        # Verify
        self.vm_service.get_image_operation_system.assert_called_once()
        self.network_service.create_network_for_vm.assert_called_once()
        self.vm_service.create_vm.assert_called_once()
        self.network_service.create_network_for_vm.assert_called_once()
        self.network_service.get_public_ip.assert_called_once()
        self.network_service.get_sandbox_virtual_network.assert_called_once()

    def test_deploy_operation_virtual_networks_validation(self):
        # Arrange
        self.vm_service.create_resource_group = Mock(return_value=True)
        self.storage_service.create_storage_account = Mock(return_value=True)
        self.storage_service.get_storage_per_resource_group = MagicMock()
        self.network_service.create_network_for_vm = MagicMock()
        self.network_service.get_public_ip = MagicMock()
        self.vm_service.create_vm = Mock()

        # Arrange 1 - more than one network
        self.network_service.get_virtual_networks = Mock(return_value=[MagicMock(), MagicMock()])

        # Act 1
        self.assertRaises(Exception,
                          self.deploy_operation.deploy,
                          DeployAzureVMResourceModel(),
                          AzureCloudProviderResourceModel(),
                          Mock(),
                          MagicMock(),
                          Mock(),
                          Mock(),
                          Mock()
                          )

        # Arrange 2 - no networks
        self.network_service.get_virtual_networks = Mock(return_value=[])

        # Act 2
        self.assertRaises(Exception,
                          self.deploy_operation.deploy,
                          DeployAzureVMResourceModel(),
                          AzureCloudProviderResourceModel(),
                          Mock(),
                          MagicMock(),
                          Mock(),
                          Mock(),
                          Mock()
                          )

    def test_should_delete_all_created_on_error(self):
        """
        This method verifies the basic deployment of vm.
        :return:
        """

        # Arrange
        self.network_service.create_network_for_vm = MagicMock()
        vnet = Mock()
        subnet = MagicMock()
        name = "name"
        subnet.name = name
        vnet.subnets = [subnet]
        reservation = Mock()
        reservation.reservation_id = name
        self.network_service.get_sandbox_virtual_network = Mock(return_value=vnet)

        self.storage_service.get_storage_per_resource_group = MagicMock()
        self.vm_service.create_vm = Mock(side_effect=Exception('Boom!'))
        self.network_service.delete_nic = Mock()
        self.network_service.delete_ip = Mock()
        self.vm_service.delete_vm = Mock()
        self.vm_service.get_image_operation_system = MagicMock()

        # Act
        self.assertRaises(Exception,
                          self.deploy_operation.deploy,
                          DeployAzureVMResourceModel(),
                          AzureCloudProviderResourceModel(),
                          reservation,
                          Mock(),
                          Mock(),
                          Mock(),
                          Mock())

        # Verify
        self.network_service.create_network_for_vm.assert_called_once()
        self.vm_service.create_vm.assert_called_once()
        self.network_service.delete_nic.assert_called_once()
        self.network_service.delete_ip.assert_called_once()
        self.vm_service.delete_vm.assert_called_once()
