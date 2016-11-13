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
        self.security_group_service = MagicMock()
        self.tags_service = TagService()
        self.deploy_operation = DeployAzureVMOperation(vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       storage_service=self.storage_service,
                                                       vm_credentials_service=self.vm_credentials_service,
                                                       key_pair_service=self.key_pair_service,
                                                       tags_service=self.tags_service,
                                                       security_group_service=self.security_group_service)

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
        self.vm_service.create_vm = MagicMock()
        self.deploy_operation._process_nsg_rules = MagicMock()
        resource_model = DeployAzureVMResourceModel()
        resource_model.add_public_ip = True
        self.network_client = MagicMock()
        self.network_client.public_ip_addresses.get = Mock()

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
                                     self.network_client,
                                     Mock(),
                                     Mock(),
                                     Mock())

        # Verify
        self.vm_service.get_image_operation_system.assert_called_once()
        self.network_service.create_network_for_vm.assert_called_once()
        self.vm_service.create_vm.assert_called_once()
        self.network_service.create_network_for_vm.assert_called_once()
        self.deploy_operation._process_nsg_rules.assert_called_once()
        self.network_client.public_ip_addresses.get.assert_called_once()
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
        self.deploy_operation._process_nsg_rules = Mock()

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

    def test_process_nsg_rules(self):
        """Check that method validates NSG is single per group and uses security group service for rules creation"""
        group_name = "test_group_name"
        network_client = MagicMock()
        azure_vm_deployment_model = MagicMock()
        nic = MagicMock()
        security_groups_list = MagicMock()
        self.deploy_operation.security_group_service.list_network_security_group.return_value = security_groups_list
        self.deploy_operation._validate_resource_is_single_per_group = MagicMock()

        # Act
        self.deploy_operation._process_nsg_rules(
            network_client=network_client,
            group_name=group_name,
            azure_vm_deployment_model=azure_vm_deployment_model,
            nic=nic)

        # Verify
        self.deploy_operation.security_group_service.list_network_security_group.assert_called_once_with(
            group_name=group_name,
            network_client=network_client)

        self.deploy_operation._validate_resource_is_single_per_group.assert_called_once_with(
            security_groups_list, group_name, 'network security group')

        self.deploy_operation.security_group_service.create_network_security_group_rules.assert_called_once_with(
            destination_addr=nic.ip_configurations[0].private_ip_address,
            group_name=group_name,
            inbound_rules=[],
            network_client=network_client,
            security_group_name=security_groups_list[0].name)

    def test_process_nsg_rules_inbound_ports_attribute_is_empty(self):
        """Check that method will not call security group service for NSG rules creation if there are no rules"""
        group_name = "test_group_name"
        network_client = MagicMock()
        azure_vm_deployment_model = MagicMock()
        nic = MagicMock()
        self.deploy_operation._validate_resource_is_single_per_group = MagicMock()
        azure_vm_deployment_model.inbound_ports = ""

        # Act
        self.deploy_operation._process_nsg_rules(
            network_client=network_client,
            group_name=group_name,
            azure_vm_deployment_model=azure_vm_deployment_model,
            nic=nic)

        # Verify
        self.deploy_operation.security_group_service.list_network_security_group.assert_not_called()
        self.deploy_operation._validate_resource_is_single_per_group.assert_not_called()
        self.deploy_operation.security_group_service.create_network_security_group_rules.assert_not_called()

    def test_validate_resource_is_single_per_group(self):
        """Check that method will not throw Exception if length of resource list is equal to 1"""
        group_name = "test_group_name"
        resource_name = MagicMock()
        resource_list = [MagicMock()]
        try:
            # Act
            self.deploy_operation._validate_resource_is_single_per_group(resource_list, group_name, resource_name)
        except Exception as e:
            # Verify
            self.fail("Method should not raise any exception. Got: {}: {}".format(type(e), e))

    def test_validate_resource_is_single_per_group_several_resources(self):
        """Check that method will not throw Exception if length of resource list is more than 1"""
        group_name = "test_group_name"
        resource_name = MagicMock()
        resource_list = [MagicMock(), MagicMock(), MagicMock()]

        with self.assertRaises(Exception):
            self.deploy_operation._validate_resource_is_single_per_group(resource_list, group_name, resource_name)

    def test_validate_resource_is_single_per_group_missing_resource(self):
        """Check that method will throw Exception if resource list is empty"""
        group_name = "test_group_name"
        resource_name = MagicMock()
        resource_list = []

        with self.assertRaises(Exception):
            self.deploy_operation._validate_resource_is_single_per_group(resource_list, group_name, resource_name)
