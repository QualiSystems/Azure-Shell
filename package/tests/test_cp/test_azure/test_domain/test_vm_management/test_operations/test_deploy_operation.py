from unittest import TestCase

from mock import MagicMock
from mock import Mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.storage_service import StorageService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import DeployAzureVMOperation
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMResourceModel


class TestDeployAzureVMOperation(TestCase):
    def setUp(self):
        self.logger = Mock()
        self.storage_service = MagicMock()
        self.vm_service = VirtualMachineService(MagicMock())
        self.network_service = NetworkService(MagicMock(), MagicMock())
        self.vm_credentials_service = Mock()
        self.key_pair_service = Mock()
        self.security_group_service = MagicMock()
        self.tags_service = TagService()
        self.name_provider_service = MagicMock()
        self.vm_extension_service = MagicMock()
        self.generic_lock_provider = MagicMock()
        self.cancellation_service = MagicMock()

        self.deploy_operation = DeployAzureVMOperation(vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       storage_service=self.storage_service,
                                                       vm_credentials_service=self.vm_credentials_service,
                                                       key_pair_service=self.key_pair_service,
                                                       tags_service=self.tags_service,
                                                       security_group_service=self.security_group_service,
                                                       name_provider_service=self.name_provider_service,
                                                       vm_extension_service=self.vm_extension_service,
                                                       generic_lock_provider=self.generic_lock_provider,
                                                       cancellation_service=self.cancellation_service)

    def test_get_sandbox_subnet(self):
        """Check that method will call network service to get sandbox vNet and will return it's subnet by given name"""
        network_client = MagicMock()
        cloud_provider_model = MagicMock()
        subnet_name = "testsubnetname"
        sandbox_subnet = MagicMock()
        sandbox_subnet.name = subnet_name
        self.network_service.get_sandbox_virtual_network = MagicMock(
            return_value=MagicMock(subnets=[MagicMock(), MagicMock(), sandbox_subnet]))

        # Act
        subnet = self.deploy_operation._get_sandbox_subnet(
            network_client=network_client,
            cloud_provider_model=cloud_provider_model,
            subnet_name=subnet_name,
            logger=self.logger)

        # Verify
        self.network_service.get_sandbox_virtual_network.assert_called_once_with(
            network_client=network_client,
            group_name=cloud_provider_model.management_group_name)

        self.assertEqual(subnet, sandbox_subnet)

    def test_get_sandbox_subnet_will_raise_no_valid_subnet_exception(self):
        """Check that method will raise Exception if there is no subnet with given name under the MGMT network"""
        network_client = MagicMock()
        cloud_provider_model = MagicMock()
        subnet_name = "testsubnetname"
        self.network_service.get_sandbox_virtual_network = MagicMock(
            return_value=MagicMock(subnets=[MagicMock(), MagicMock(), MagicMock()]))

        with self.assertRaises(Exception):
            self.deploy_operation._get_sandbox_subnet(
                network_client=network_client,
                cloud_provider_model=cloud_provider_model,
                subnet_name=subnet_name)

    def test_get_public_ip_address(self):
        """Check that method will use network service to get Public IP by it's name"""
        network_client = MagicMock()
        azure_vm_deployment_model = MagicMock(add_public_ip=True)
        group_name = "testgroupname"
        ip_name = "testipname"
        expected_ip_addr = "10.10.10.10"
        public_ip = MagicMock(ip_address=expected_ip_addr)
        cancellation_context = MagicMock()
        self.network_service.get_public_ip = MagicMock(return_value=public_ip)

        # Act
        ip_addr = self.deploy_operation._get_public_ip_address(
            network_client=network_client,
            azure_vm_deployment_model=azure_vm_deployment_model,
            group_name=group_name,
            ip_name=ip_name,
            cancellation_context=cancellation_context,
            logger=self.logger)

        # Verify
        self.assertEqual(ip_addr, expected_ip_addr)

    def test_get_public_ip_address_add_public_ip_is_false(self):
        """Check that method will return None if "add_public_ip" attribute is False"""
        network_client = MagicMock()
        azure_vm_deployment_model = MagicMock(add_public_ip=False)
        group_name = "testgroupname"
        ip_name = "testipname"
        cancellation_context = MagicMock()
        self.network_service.get_public_ip = MagicMock()

        # Act
        ip_addr = self.deploy_operation._get_public_ip_address(
            network_client=network_client,
            azure_vm_deployment_model=azure_vm_deployment_model,
            group_name=group_name,
            ip_name=ip_name,
            cancellation_context=cancellation_context,
            logger=self.logger)

        # Verify
        self.assertIsNone(ip_addr)
        self.network_service.get_public_ip.assert_not_called()

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
        self.vm_service.get_virtual_machine_image = MagicMock()
        self.vm_service.create_vm = MagicMock()
        self.deploy_operation._process_nsg_rules = MagicMock()
        resource_model = DeployAzureVMResourceModel()
        resource_model.add_public_ip = True
        self.network_client = MagicMock()
        self.network_client.public_ip_addresses.get = Mock()
        self.deploy_operation._prepare_vm_size = MagicMock()

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
                                     Mock(),
                                     Mock())

        # Verify
        self.vm_service.get_virtual_machine_image.assert_called_once()
        self.network_service.create_network_for_vm.assert_called_once()
        self.vm_service.create_vm.assert_called_once()
        self.network_service.create_network_for_vm.assert_called_once()
        self.deploy_operation._process_nsg_rules.assert_called_once()
        self.network_client.public_ip_addresses.get.assert_called_once()
        self.network_service.get_sandbox_virtual_network.assert_called_once()
        self.cancellation_service.check_if_cancelled.assert_called()

    def test_deploy_from_custom_image(self):
        """Check deploy from custom Image operation"""
        azure_vm_deployment_model = MagicMock(app_name="")
        cloud_provider_model = MagicMock()
        reservation = MagicMock()
        network_client = MagicMock()
        compute_client = MagicMock()
        storage_client = MagicMock()
        logger = MagicMock()
        cancellation_context = MagicMock()

        self.deploy_operation._get_sandbox_subnet = MagicMock()
        self.deploy_operation._get_sandbox_storage_account_name = MagicMock()
        self.deploy_operation._process_nsg_rules = MagicMock()
        self.deploy_operation._get_public_ip_address = MagicMock()
        self.storage_service.copy_blob = MagicMock()
        self.network_service.create_network_for_vm = MagicMock()
        self.vm_credentials_service.prepare_credentials = MagicMock()
        self.vm_service.create_vm_from_custom_image = MagicMock()
        self.network_client = MagicMock()

        # Act
        self.deploy_operation.deploy_from_custom_image(
            azure_vm_deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            reservation=reservation,
            network_client=network_client,
            compute_client=compute_client,
            storage_client=storage_client,
            cancellation_context=cancellation_context,
            logger=logger)

        # Verify
        self.storage_service.copy_blob.assert_called_once()
        self.network_service.create_network_for_vm.assert_called_once()
        self.vm_service.create_vm_from_custom_image.assert_called_once()
        self.network_service.create_network_for_vm.assert_called_once()
        self.deploy_operation._process_nsg_rules.assert_called_once()
        self.deploy_operation._get_public_ip_address.assert_called_once()
        self.deploy_operation._get_sandbox_subnet.assert_called_once()
        self.deploy_operation.storage_service.get_sandbox_storage_account_name.assert_called_once()
        self.cancellation_service.check_if_cancelled.assert_called_with(cancellation_context)

    def test_deploy_from_custom_image_delete_all_resources_on_error(self):
        """Check that method will delete all created resources in case of any Exception occurs while deploying"""
        azure_vm_deployment_model = MagicMock(app_name="")
        cloud_provider_model = MagicMock()
        reservation = MagicMock()
        network_client = MagicMock()
        compute_client = MagicMock()
        storage_client = MagicMock()
        test_name = "test_generated_name"
        logger = MagicMock()
        cancellation_context = MagicMock()
        self.name_provider_service.generate_name.return_value = test_name
        self.deploy_operation._rollback_deployed_resources = MagicMock()
        self.deploy_operation._get_sandbox_subnet = MagicMock()
        self.deploy_operation._get_sandbox_storage_account_name = MagicMock()
        self.deploy_operation._process_nsg_rules = MagicMock()
        self.storage_service.copy_blob = MagicMock()
        self.network_service.create_network_for_vm = MagicMock(side_effect=Exception)

        with self.assertRaises(Exception):
            # Act
            self.deploy_operation.deploy_from_custom_image(
                azure_vm_deployment_model=azure_vm_deployment_model,
                cloud_provider_model=cloud_provider_model,
                reservation=reservation,
                network_client=network_client,
                compute_client=compute_client,
                storage_client=storage_client,
                cancellation_context=cancellation_context,
                logger=logger)

        # Verify
        self.deploy_operation._rollback_deployed_resources.assert_called_once_with(
            compute_client=compute_client,
            group_name=str(reservation.reservation_id),
            interface_name=test_name,
            ip_name=test_name,
            network_client=network_client,
            vm_name=test_name,
            cancellation_context=cancellation_context,
            logger=logger)

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
        self.vm_service.get_virtual_machine_image = MagicMock()
        self.deploy_operation._process_nsg_rules = Mock()
        self.deploy_operation._rollback_deployed_resources = MagicMock()
        self.deploy_operation._prepare_vm_size = MagicMock()
        self.deploy_operation.cancellation_service.check_if_cancelled.return_value = False

        # Act
        self.assertRaises(Exception,
                          self.deploy_operation.deploy,
                          DeployAzureVMResourceModel(),
                          AzureCloudProviderResourceModel(),
                          reservation,
                          Mock(),
                          Mock(),
                          Mock(),
                          Mock(),
                          Mock())

        # Verify
        self.network_service.create_network_for_vm.assert_called_once()
        self.vm_service.create_vm.assert_called_once()
        self.deploy_operation._rollback_deployed_resources.assert_called_once()

    def test_rollback_deployed_resources(self):
        """Check that deploy rollback method will delete resources"""
        self.network_service.delete_nic = Mock()
        self.network_service.delete_ip = Mock()
        self.vm_service.delete_vm = Mock()

        # Act
        self.deploy_operation._rollback_deployed_resources(compute_client=MagicMock(),
                                                           network_client=MagicMock(),
                                                           group_name=MagicMock(),
                                                           interface_name=MagicMock(),
                                                           vm_name=MagicMock(),
                                                           ip_name=MagicMock(),
                                                           cancellation_context=MagicMock(),
                                                           logger=MagicMock())

        # Verify
        self.network_service.delete_nic.assert_called_once()
        self.network_service.delete_ip.assert_called_once()
        self.vm_service.delete_vm.assert_called_once()

    def test_process_nsg_rules(self):
        """Check that method validates NSG is single per group and uses security group service for rules creation"""
        group_name = "test_group_name"
        network_client = MagicMock()
        azure_vm_deployment_model = MagicMock()
        nic = MagicMock()
        cancellation_context = MagicMock()
        logger = MagicMock()
        security_groups_list = MagicMock()
        self.deploy_operation.security_group_service.list_network_security_group.return_value = security_groups_list
        self.deploy_operation._validate_resource_is_single_per_group = MagicMock()
        self.deploy_operation.security_group_service.get_network_security_group.return_value = security_groups_list[0]
        lock = Mock()
        self.generic_lock_provider.get_resource_lock=Mock(return_value=lock)

        # Act
        self.deploy_operation._process_nsg_rules(
            network_client=network_client,
            group_name=group_name,
            azure_vm_deployment_model=azure_vm_deployment_model,
            nic=nic,
            cancellation_context=cancellation_context,
            logger=logger)

        # Verify
        self.deploy_operation.security_group_service.get_network_security_group.assert_called_once_with(
            network_client=network_client,
            group_name=group_name)

        self.deploy_operation.security_group_service.create_network_security_group_rules.assert_called_once_with(
            destination_addr=nic.ip_configurations[0].private_ip_address,
            group_name=group_name,
            inbound_rules=[],
            network_client=network_client,
            security_group_name=security_groups_list[0].name,
            lock=lock)

    def test_process_nsg_rules_inbound_ports_attribute_is_empty(self):
        """Check that method will not call security group service for NSG rules creation if there are no rules"""
        group_name = "test_group_name"
        network_client = MagicMock()
        azure_vm_deployment_model = MagicMock()
        nic = MagicMock()
        cancellation_context = MagicMock()
        logger = MagicMock()
        self.deploy_operation._validate_resource_is_single_per_group = MagicMock()
        azure_vm_deployment_model.inbound_ports = ""

        # Act
        self.deploy_operation._process_nsg_rules(
            network_client=network_client,
            group_name=group_name,
            azure_vm_deployment_model=azure_vm_deployment_model,
            nic=nic,
            cancellation_context=cancellation_context,
            logger=logger)

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

    def test_validate_deployment_model_raises_exception(self):
        """Check that method will raise Exception if "Add Public IP" attr is False and "Inbound Ports" is not empty"""
        vm_deployment_mode = MagicMock(inbound_ports="80:tcp", add_public_ip=False)

        with self.assertRaises(Exception):
            self.deploy_operation._validate_deployment_model(vm_deployment_mode)

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

    def test_prepare_computer_name(self):
        """Check that method will use NameProviderService.generate_name to process computer name"""
        computer_name = MagicMock()
        self.name_provider_service.generate_name.return_value = computer_name
        name = "test_name"
        # Act
        res = self.deploy_operation._prepare_computer_name(name)
        # Verify
        self.name_provider_service.generate_name.assert_called_once_with(name, length=15)
        self.assertEqual(res, computer_name)

    def test_prepare_vm_size_retrieve_attr_from_deployment_model(self):
        """Check that method will retrieve "vm_size" attribute from deployment model if attr is not empty"""
        expected_vm_size = MagicMock()
        cloud_provider_model = MagicMock(vm_size="")
        azure_vm_deployment_model = MagicMock(vm_size=expected_vm_size)
        # Act
        res = self.deploy_operation._prepare_vm_size(azure_vm_deployment_model=azure_vm_deployment_model,
                                                     cloud_provider_model=cloud_provider_model)
        # Verify
        self.assertEqual(res, expected_vm_size)

    def test_prepare_vm_size_retrieve_default_attr_from_cp_model(self):
        """Check that method will retrieve "vm_size" attr from cp model if no such one in the deployment model"""
        expected_vm_size = MagicMock()
        cloud_provider_model = MagicMock(vm_size=expected_vm_size)
        azure_vm_deployment_model = MagicMock(vm_size="")
        # Act
        res = self.deploy_operation._prepare_vm_size(azure_vm_deployment_model=azure_vm_deployment_model,
                                                     cloud_provider_model=cloud_provider_model)
        # Verify
        self.assertEqual(res, expected_vm_size)

    def test_prepare_vm_size_attr_is_empty(self):
        """Check that method will raise exception if "vm_size" attr is empty in both cp and deployment models"""
        cloud_provider_model = MagicMock(vm_size="")
        azure_vm_deployment_model = MagicMock(vm_size="")

        with self.assertRaises(Exception):
            self.deploy_operation._prepare_vm_size(azure_vm_deployment_model=azure_vm_deployment_model,
                                                   cloud_provider_model=cloud_provider_model)
