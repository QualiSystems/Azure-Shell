from unittest import TestCase

from azure.mgmt.compute.models import OperatingSystemTypes
from azure.mgmt.network.models import VirtualNetwork
from cloudshell.cp.core.models import Attribute
from mock import MagicMock
from mock import Mock

from cloudshell.cp.azure.domain.services.ip_service import IpService
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import DeployAzureVMOperation
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMResourceModel
from cloudshell.cp.azure.models.nic_request import NicRequest


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
        self.image_data_factory = MagicMock()
        self.vm_details_provider = MagicMock()
        self.ip_service = IpService(self.generic_lock_provider)

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
                                                       cancellation_service=self.cancellation_service,
                                                       image_data_factory=self.image_data_factory,
                                                       vm_details_provider=self.vm_details_provider,
                                                       ip_service=self.ip_service)

    def test_get_sandbox_subnet_with_multiple_subnet_mode(self):
        """Check that method will call network service to get sandbox vNet and will return it's subnet by given name"""
        network_client = MagicMock()
        cloud_provider_model = MagicMock()
        deployment_model, sandbox_subnet, subnet_name = self._prepare_mock_subnets()
        self.network_service.get_sandbox_virtual_network = MagicMock(
            return_value=MagicMock(subnets=[MagicMock(), MagicMock(), sandbox_subnet]))

        # Act
        subnets = self.deploy_operation._get_nic_requests(
            network_client=network_client,
            cloud_provider_model=cloud_provider_model,
            logger=self.logger,
            deployment_model=deployment_model,
            resource_group_name="some_resource_group",
            vm_name="whatever")

        # Verify
        self.network_service.get_sandbox_virtual_network.assert_called_once_with(
            network_client=network_client,
            group_name=cloud_provider_model.management_group_name)

        self.assertEqual(subnets[0].subnet, sandbox_subnet)

    def test_get_sandbox_subnet_with_single_subnet_node(self):
        """Check that method will call network service to get sandbox vNet and will return it's subnet by given name"""
        resource_group_name = "some_resource_group"
        network_client = MagicMock()
        cloud_provider_model = MagicMock()
        deployment_model, sandbox_subnet, subnet_name = self._prepare_mock_subnets()
        deployment_model.network_configurations = None  # single subnet mode
        sandbox_subnet.name = resource_group_name

        self.network_service.get_sandbox_virtual_network = MagicMock(
            return_value=MagicMock(subnets=[sandbox_subnet]))

        # Act
        subnets = self.deploy_operation._get_nic_requests(
            network_client=network_client,
            cloud_provider_model=cloud_provider_model,
            logger=self.logger,
            deployment_model=deployment_model,
            resource_group_name=resource_group_name,
            vm_name="whatever")

        # Verify
        self.network_service.get_sandbox_virtual_network.assert_called_once_with(
            network_client=network_client,
            group_name=cloud_provider_model.management_group_name)

        self.assertEqual(subnets[0].subnet, sandbox_subnet)

    def _prepare_mock_subnets(self):
        subnet_name = "testsubnetname"
        sandbox_subnet = MagicMock()
        sandbox_subnet.name = subnet_name
        deployment_model = Mock()
        network_action = Mock()
        network_action.connection_params.subnet_id = subnet_name
        deployment_model.network_configurations = [network_action]

        return deployment_model, sandbox_subnet, subnet_name

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

    def test_deploy_vm_generic(self):
        """
        This method verifies the basic deployment of vm.
        :return:
        """
        # Arrange
        resource_model = DeployAzureVMResourceModel()
        data = Mock()
        data.nic_requests = [NicRequest("a", Mock(), True)]
        updated_data = Mock()
        updated_data.vm_credentials = Mock()
        first_interface_name = 'a'
        updated_data.nic_requests = [NicRequest("a", Mock(), True)]
        updated_data.ip_name = updated_data.public_ip_address = '{}_PublicIP'.format(first_interface_name)
        updated_data.primary_private_ip_address = 'lol'
        deployed_app_attributes = Mock()
        self.deploy_operation._prepare_deploy_data = Mock(return_value=data)
        self.deploy_operation._create_vm_common_objects = Mock(return_value=updated_data)
        self.deploy_operation._create_vm_custom_script_extension = Mock()
        self.deploy_operation._prepare_deployed_app_attributes = Mock(return_value=deployed_app_attributes)
        self.deploy_operation._get_public_ip_address = Mock(return_value="pub_ip_address")

        vm = Mock()
        create_vm_action = Mock(return_value=vm)

        cancellation_context = Mock()
        reservation = Mock()
        cloud_provider_model = Mock()
        logger = Mock()
        network_client = Mock()
        compute_client = Mock()
        storage_client = Mock()
        cloudshell_session = Mock()
        network_actions = []

        # Act
        result = self.deploy_operation._deploy_vm_generic(create_vm_action=create_vm_action,
                                                          deployment_model=resource_model,
                                                          cloud_provider_model=cloud_provider_model,
                                                          reservation=reservation,
                                                          storage_client=storage_client,
                                                          compute_client=compute_client,
                                                          network_client=network_client,
                                                          cancellation_context=cancellation_context,
                                                          logger=logger,
                                                          cloudshell_session=cloudshell_session,
                                                          network_actions=network_actions)

        # Verify
        self.assertEquals(self.cancellation_service.check_if_cancelled.call_count, 2)
        self.cancellation_service.check_if_cancelled.assert_called_with(cancellation_context)
        self.deploy_operation._prepare_deploy_data.assert_called_once_with(
            logger=logger,
            reservation=reservation,
            deployment_model=resource_model,
            cloud_provider_model=cloud_provider_model,
            network_client=network_client,
            storage_client=storage_client,
            compute_client=compute_client,
            network_actions=network_actions)
        self.deploy_operation._create_vm_common_objects.assert_called_once_with(
            logger=logger,
            data=data,
            deployment_model=resource_model,
            cloud_provider_model=cloud_provider_model,
            network_client=network_client,
            storage_client=storage_client,
            cancellation_context=cancellation_context,
            cloudshell_session=cloudshell_session)
        create_vm_action.assert_called_once_with(
            deployment_model=resource_model,
            cloud_provider_model=cloud_provider_model,
            data=updated_data,
            compute_client=compute_client,
            cancellation_context=cancellation_context,
            logger=logger)
        self.deploy_operation._create_vm_custom_script_extension.assert_called_once_with(
            deployment_model=resource_model,
            cloud_provider_model=cloud_provider_model,
            compute_client=compute_client,
            data=updated_data,
            logger=logger,
            cancellation_context=cancellation_context)
        self.deploy_operation._get_public_ip_address.assert_called_once_with(
            network_client=network_client,
            azure_vm_deployment_model=resource_model,
            group_name=updated_data.group_name,
            ip_name=updated_data.ip_name,
            cancellation_context=cancellation_context,
            logger=logger)
        self.deploy_operation._prepare_deployed_app_attributes.assert_called_once_with(
            admin_username=updated_data.vm_credentials.admin_username,
            admin_password=updated_data.vm_credentials.admin_password,
            public_ip=updated_data.public_ip_address
        )
        self.assertEquals(updated_data.public_ip_address, "pub_ip_address")
        self.assertEquals(result.vmName, updated_data.vm_name)
        self.assertEquals(result.vmUuid, vm.vm_id)
        self.assertEquals(result.deployedAppAttributes, deployed_app_attributes)
        self.assertEquals(result.deployedAppAddress, updated_data.primary_private_ip_address)

    def test_deploy_from_custom_image(self):
        # Arrange
        expected_result = Mock()
        self.deploy_operation._deploy_vm_generic = Mock(return_value=expected_result)
        self.deploy_operation._create_vm_custom_image_action = Mock()
        azure_vm_deployment_model = Mock()
        cloud_provider_model = Mock()
        reservation = Mock()
        network_client = Mock()
        compute_client = Mock()
        storage_client = Mock()
        cancellation_context = Mock()
        logger = Mock()
        cloudshell_session = Mock()
        network_actions = []

        # Act
        res = self.deploy_operation.deploy_from_custom_image(
            deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            reservation=reservation,
            network_client=network_client,
            compute_client=compute_client,
            storage_client=storage_client,
            cancellation_context=cancellation_context,
            logger=logger,
            cloudshell_session=cloudshell_session,
            network_actions=network_actions)

        # Assert
        self.assertEquals(expected_result, res)
        self.deploy_operation._deploy_vm_generic.assert_called_once_with(
            create_vm_action=self.deploy_operation._create_vm_custom_image_action,
            deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            reservation=reservation,
            storage_client=storage_client,
            compute_client=compute_client,
            network_client=network_client,
            cancellation_context=cancellation_context,
            logger=logger,
            cloudshell_session=cloudshell_session,
            network_actions=network_actions)

    def test_deploy_from_marketplace(self):
        # Arrange
        expected_result = Mock()
        self.deploy_operation._deploy_vm_generic = Mock(return_value=expected_result)
        self.deploy_operation._create_vm_custom_image_action = Mock()
        azure_vm_deployment_model = Mock()
        cloud_provider_model = Mock()
        reservation = Mock()
        network_client = Mock()
        compute_client = Mock()
        storage_client = Mock()
        cancellation_context = Mock()
        logger = Mock()
        cloudshell_session = Mock()
        network_actions = []

        # Act
        res = self.deploy_operation.deploy_from_marketplace(deployment_model=azure_vm_deployment_model,
                                                            cloud_provider_model=cloud_provider_model,
                                                            reservation=reservation, network_client=network_client,
                                                            compute_client=compute_client,
                                                            storage_client=storage_client,
                                                            cancellation_context=cancellation_context, logger=logger,
                                                            cloudshell_session=cloudshell_session,
                                                            network_actions=network_actions)

        # Assert
        self.assertEquals(expected_result, res)
        self.deploy_operation._deploy_vm_generic.assert_called_once_with(
            create_vm_action=self.deploy_operation._create_vm_marketplace_action,
            deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            reservation=reservation,
            storage_client=storage_client,
            compute_client=compute_client,
            network_client=network_client,
            cancellation_context=cancellation_context,
            logger=logger,
            cloudshell_session=cloudshell_session,
            network_actions=network_actions)

    def test_create_vm_custom_image_action(self):
        """Check deploy from custom Image operation"""
        # Arrange
        azure_vm_deployment_model = MagicMock()
        azure_vm_deployment_model.image_name = "some_image"
        azure_vm_deployment_model.image_resource_group = "image_group"

        cloud_provider_model = MagicMock()
        logger = MagicMock()
        compute_client = Mock()
        cancellation_context = MagicMock()
        data = Mock()
        data.group_name = "group"

        self.vm_service.create_vm_from_custom_image = Mock()

        # Act
        self.deploy_operation._create_vm_custom_image_action(
            compute_client=compute_client,
            deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            data=data,
            cancellation_context=cancellation_context,
            logger=logger)

        # Verify
        self.cancellation_service.check_if_cancelled.assert_called_with(cancellation_context)
        self.cancellation_service.check_if_cancelled.assert_called()
        self.vm_service.create_vm_from_custom_image.assert_called_once_with(
            compute_management_client=compute_client,
            image_name=azure_vm_deployment_model.image_name,
            image_resource_group=azure_vm_deployment_model.image_resource_group,
            disk_size=azure_vm_deployment_model.disk_size,
            disk_type=azure_vm_deployment_model.disk_type,
            vm_credentials=data.vm_credentials,
            computer_name=data.computer_name,
            group_name=data.group_name,
            nics=data.nics,
            region=cloud_provider_model.region,
            vm_name=data.vm_name,
            tags=data.tags,
            vm_size=data.vm_size,
            cancellation_context=cancellation_context,
            logger=logger)

    def test_create_vm_marketplace_action(self):
        """Check deploy from custom Image operation"""
        # Arrange
        azure_vm_deployment_model = MagicMock()
        cloud_provider_model = MagicMock()
        logger = MagicMock()
        compute_client = Mock()
        cancellation_context = MagicMock()
        data = Mock()
        self.vm_service.create_vm_from_marketplace = Mock()

        # Act
        self.deploy_operation._create_vm_marketplace_action(
            compute_client=compute_client,
            deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            data=data,
            cancellation_context=cancellation_context,
            logger=logger)

        # Verify
        self.vm_service.create_vm_from_marketplace.assert_called_once_with(
            compute_management_client=compute_client,
            image_offer=azure_vm_deployment_model.image_offer,
            image_publisher=azure_vm_deployment_model.image_publisher,
            image_sku=azure_vm_deployment_model.image_sku,
            image_version=azure_vm_deployment_model.image_version,
            disk_type=azure_vm_deployment_model.disk_type,
            disk_size=azure_vm_deployment_model.disk_size,
            vm_credentials=data.vm_credentials,
            computer_name=data.computer_name,
            group_name=data.group_name,
            nics=data.nics,
            region=cloud_provider_model.region,
            vm_name=data.vm_name,
            tags=data.tags,
            vm_size=data.vm_size,
            purchase_plan=data.image_model.purchase_plan,
            cancellation_context=cancellation_context)

    def test_deploy_vm_generic_delete_all_resources_on_error(self):
        """ Check that method will delete all created resources in case of any Exception occurs while deploying"""
        # Arrange
        resource_model = DeployAzureVMResourceModel()
        data = Mock()
        updated_data = Mock()
        updated_data.vm_credentials = Mock()
        deployed_app_attributes = Mock()
        self.deploy_operation._prepare_deploy_data = Mock(return_value=data)
        self.deploy_operation._create_vm_common_objects = Mock(return_value=updated_data)
        self.deploy_operation._create_vm_custom_script_extension = Mock()
        self.deploy_operation._prepare_deployed_app_attributes = Mock(return_value=deployed_app_attributes)

        cancellation_context = Mock()
        reservation = Mock()
        cloud_provider_model = Mock()
        logger = Mock()
        network_client = Mock()
        compute_client = Mock()
        storage_client = Mock()
        cloudshell_session = Mock()
        create_vm_action = Mock(side_effect=Exception)
        self.deploy_operation._rollback_deployed_resources = Mock()
        network_actions = []

        # Act
        with self.assertRaises(Exception):
            self.deploy_operation._deploy_vm_generic(create_vm_action=create_vm_action,
                                                     deployment_model=resource_model,
                                                     cloud_provider_model=cloud_provider_model,
                                                     reservation=reservation,
                                                     storage_client=storage_client,
                                                     compute_client=compute_client,
                                                     network_client=network_client,
                                                     cancellation_context=cancellation_context,
                                                     logger=logger,
                                                     cloudshell_session=cloudshell_session,
                                                     network_actions=network_actions)

        # Verify
        self.deploy_operation._rollback_deployed_resources.assert_called_once_with(
            compute_client=compute_client,
            network_client=network_client,
            group_name=updated_data.group_name,
            nic_requests=updated_data.nic_requests,
            vm_name=updated_data.vm_name,
            logger=logger,
            private_ip_allocation_method=cloud_provider_model.private_ip_allocation_method,
            allocated_private_ips=updated_data.all_private_ip_addresses,
            reservation_id=updated_data.reservation_id,
            cloudshell_session=cloudshell_session)

    def test_deploy_operation_virtual_networks_validation(self):
        # todo - add tests for validations
        pass

    def test_rollback_deployed_resources(self):
        """Check that deploy rollback method will delete resources"""
        self.network_service.delete_nic = Mock()
        self.network_service.delete_ip = Mock()
        self.vm_service.delete_vm = Mock()
        private_ip_allocation_method = "Static"
        cloudshell_session = Mock()

        # Act
        self.deploy_operation._rollback_deployed_resources(logger=MagicMock(),
                                                           compute_client=MagicMock(),
                                                           network_client=MagicMock(),
                                                           group_name=MagicMock(),
                                                           nic_requests=[MagicMock()],
                                                           vm_name=MagicMock(),
                                                           private_ip_allocation_method=private_ip_allocation_method,
                                                           allocated_private_ips=[],
                                                           reservation_id=Mock(),
                                                           cloudshell_session=cloudshell_session
                                                           )

        # Verify
        self.network_service.delete_nic.assert_called_once()
        self.network_service.delete_ip.assert_called_once()
        self.vm_service.delete_vm.assert_called_once()
        cloudshell_session.ReleaseFromPool.assert_called_once()


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
        os_type = Mock()
        network_actions = []

        with self.assertRaises(Exception):
            self.deploy_operation._validate_deployment_model(vm_deployment_mode,
                                                             os_type=os_type,
                                                             network_actions=network_actions)

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

    def test_prepare_computer_name_win(self):
        """
        Check that method will use NameProviderService.generate_name to process computer name and correct length is
        selected based on the OS type
        """
        computer_name = MagicMock()
        self.name_provider_service.generate_name = Mock(return_value=computer_name)
        os_type = OperatingSystemTypes.windows
        postfix = Mock()
        name = "test_name"
        # Act
        res = self.deploy_operation._prepare_computer_name(name=name, postfix=postfix, os_type=os_type)
        # Verify
        self.name_provider_service.generate_name.assert_called_once_with(name=name, postfix=postfix, max_length=15)
        self.assertEqual(res, computer_name)

    def test_prepare_computer_name_linux(self):
        """
        Check that method will use NameProviderService.generate_name to process computer name and correct length is
        selected based on the OS type
        """
        computer_name = MagicMock()
        self.name_provider_service.generate_name = Mock(return_value=computer_name)
        os_type = OperatingSystemTypes.linux
        postfix = Mock()
        name = "test_name"
        # Act
        res = self.deploy_operation._prepare_computer_name(name=name, postfix=postfix, os_type=os_type)
        # Verify
        self.name_provider_service.generate_name.assert_called_once_with(name=name, postfix=postfix, max_length=64)
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

    def test_prepare_deploy_data(self):
        # Arrange
        deployment_model = MagicMock(app_name="Cool App")
        image_data_model = Mock()
        self.deploy_operation.image_data_factory.get_image_data_model = Mock(return_value=image_data_model)
        self.deploy_operation._validate_deployment_model = Mock()
        self.deploy_operation.name_provider_service.generate_name = Mock(return_value="random_name")
        self.deploy_operation._prepare_computer_name = Mock(return_value="computer_name")
        self.deploy_operation._prepare_vm_size = Mock(return_value="vm_size")
        self.deploy_operation._get_nic_requests = Mock(return_value=[NicRequest('random_name-0', Mock(), True),
                                                                     NicRequest('random_name-1', Mock(), True)])
        self.deploy_operation.storage_service.get_sandbox_storage_account_name = Mock(return_value="storage")
        self.deploy_operation.tags_service.get_tags = Mock()
        self.name_provider_service.normalize_name = Mock(return_value="cool-app")
        logger = Mock()
        reservation_id = "res_id"
        reservation = MagicMock(reservation_id=reservation_id)
        cloud_provider_model = Mock()
        network_client = Mock()
        storage_client = Mock()
        compute_client = Mock()
        network_actions = []

        # Act
        data = self.deploy_operation._prepare_deploy_data(
            logger=logger,
            reservation=reservation,
            deployment_model=deployment_model,
            cloud_provider_model=cloud_provider_model,
            network_client=network_client,
            storage_client=storage_client,
            compute_client=compute_client,
            network_actions=network_actions)

        # Assert
        self.deploy_operation.image_data_factory.get_image_data_model.assert_called_once_with(
            cloud_provider_model=cloud_provider_model,
            deployment_model=deployment_model,
            compute_client=compute_client,
            logger=logger)
        self.deploy_operation._validate_deployment_model.assert_called_once_with(vm_deployment_model=deployment_model,
                                                                                 os_type=image_data_model.os_type,
                                                                                 network_actions=network_actions)
        self.deploy_operation._prepare_vm_size.assert_called_once()
        self.deploy_operation._prepare_vm_size._get_sandbox_subnet()
        self.deploy_operation.storage_service.get_sandbox_storage_account_name()
        self.deploy_operation.tags_service.get_tags()
        self.assertEquals(data.reservation_id, reservation_id)
        self.assertEquals(data.group_name, reservation_id)
        self.assertEquals(data.image_model, image_data_model)
        self.name_provider_service.normalize_name.assert_called_once_with(deployment_model.app_name)
        self.assertEquals(data.app_name, "cool-app")
        self.assertEquals(data.nic_requests[0].interface_name, "random_name-0")
        self.assertEquals(data.nic_requests[1].interface_name, "random_name-1")
        self.assertEquals(data.computer_name, "computer_name")
        self.assertEquals(data.vm_name, "random_name")
        self.assertEquals(data.vm_size, "vm_size")
        self.assertEquals(data.nic_requests[0], self.deploy_operation._get_nic_requests(network_client,
                                                                                               cloud_provider_model,
                                                                                               logger,
                                                                                               deployment_model,
                                                                                               data.group_name,
                                                                                               data.app_name)[0])
        self.assertEquals(data.storage_account_name, "storage")
        self.assertEquals(data.tags, self.deploy_operation.tags_service.get_tags.return_value)

    def test_vm_common_objects(self):
        # Arrange
        logger = Mock()
        data = Mock()
        data.vm_name = 'lol'
        interface_name = 'hi'
        data.interface_names = [interface_name]
        nic_request = NicRequest(interface_name, Mock(), True)
        data.nic_requests = [nic_request]
        deployment_model = Mock()
        deployment_model.inbound_ports = '1;2-5'
        deployment_model.add_public_ip = True
        deployment_model.allow_all_sandbox_traffic = 'False'
        cloud_provider_model = Mock()
        cloud_provider_model.additional_mgmt_networks = [Mock()]
        network_client = Mock()
        network_client.virtual_networks.list.return_value = [VirtualNetwork(id='5', tags=Mock())]
        storage_client = Mock()
        cancellation_context = Mock()
        nic = Mock()
        nic.ip_configurations = [Mock()]

        self.deploy_operation.network_service.create_network_for_vm = Mock(return_value=nic)
        vm_nsg = Mock()
        self.security_group_service.create_network_security_group = Mock(return_value=vm_nsg)
        credentials = Mock()
        management_vnet = Mock()
        management_vnet.address_space.address_prefixes = [Mock()]
        self.deploy_operation.vm_credentials_service.prepare_credentials = Mock(return_value=credentials)
        self.deploy_operation.network_service.get_virtual_network_by_tag = Mock(return_value=management_vnet)
        cloudshell_session = Mock()

        # Act
        data_res = self.deploy_operation._create_vm_common_objects(
            logger=logger,
            data=data,
            deployment_model=deployment_model,
            cloud_provider_model=cloud_provider_model,
            network_client=network_client,
            storage_client=storage_client,
            cancellation_context=cancellation_context,
            cloudshell_session=cloudshell_session)

        # Assert

        self.deploy_operation.cancellation_service.check_if_cancelled.assert_called_with(cancellation_context)
        self.assertEquals(self.deploy_operation.cancellation_service.check_if_cancelled.call_count, 2)
        self.deploy_operation.network_service.create_network_for_vm.assert_called_once_with(
            network_client=network_client,
            group_name=data.group_name,
            interface_name=interface_name,
            ip_name=interface_name + '_PublicIP',
            cloud_provider_model=cloud_provider_model,
            network_security_group=vm_nsg,
            subnet=data.nic_requests[0].subnet,
            add_public_ip=deployment_model.add_public_ip,
            public_ip_type=deployment_model.public_ip_type,
            tags=data.tags,
            logger=logger,
            reservation_id=data_res.reservation_id,
            cloudshell_session=cloudshell_session)

        self.deploy_operation.vm_credentials_service.prepare_credentials.assert_called_once_with(
            os_type=data.image_model.os_type,
            username=deployment_model.username,
            password=deployment_model.password,
            storage_service=self.storage_service,
            key_pair_service=self.key_pair_service,
            storage_client=storage_client,
            group_name=data.group_name,
            storage_name=data.storage_account_name)
        self.assertEquals(data_res.nics[0], nic)
        self.assertEquals(data_res.primary_private_ip_address, nic.ip_configurations[0].private_ip_address)
        self.assertEquals(data_res.vm_credentials, credentials)

    def test_create_vm_custom_script_extension_no_ext_script_file(self):
        # Assert
        deployment_model = Mock()
        deployment_model.extension_script_file = ""
        cloud_provider_model = Mock()
        compute_client = Mock()
        data = Mock()
        logger = Mock()
        cancellation_context = Mock()
        self.deploy_operation.vm_extension_service.create_script_extension = Mock()

        # Act
        self.deploy_operation._create_vm_custom_script_extension(
            deployment_model=deployment_model,
            cloud_provider_model=cloud_provider_model,
            compute_client=compute_client,
            data=data,
            logger=logger,
            cancellation_context=cancellation_context)

        # Assert
        self.deploy_operation.vm_extension_service.create_script_extension.assert_not_called()
        self.deploy_operation.cancellation_service.check_if_cancelled.assert_not_called()

    def test_create_vm_custom_script_extension(self):
        # Assert
        deployment_model = Mock()
        cloud_provider_model = Mock()
        compute_client = Mock()
        data = Mock()
        logger = Mock()
        cancellation_context = Mock()
        self.deploy_operation.vm_extension_service.create_script_extension = Mock()

        # Act
        self.deploy_operation._create_vm_custom_script_extension(
            deployment_model=deployment_model,
            cloud_provider_model=cloud_provider_model,
            compute_client=compute_client,
            data=data,
            logger=logger,
            cancellation_context=cancellation_context)

        # Assert
        self.deploy_operation.cancellation_service.check_if_cancelled.assert_called_with(cancellation_context)
        self.assertEquals(self.deploy_operation.cancellation_service.check_if_cancelled.call_count, 2)
        self.deploy_operation.vm_extension_service.create_script_extension.assert_called_once_with(
            compute_client=compute_client,
            location=cloud_provider_model.region,
            group_name=data.group_name,
            vm_name=data.vm_name,
            image_os_type=data.image_model.os_type,
            script_file=deployment_model.extension_script_file,
            script_configurations=deployment_model.extension_script_configurations,
            tags=data.tags,
            cancellation_context=cancellation_context,
            timeout=deployment_model.extension_script_timeout)

    def test_validate_deployment_model_throws_when_has_inbound_ports_without_public_ip(self):
        # Arrange
        deployment_model = Mock()
        deployment_model.inbound_ports = "xxx"
        deployment_model.add_public_ip = None
        os_type = Mock()
        network_actions = []

        # Act & Assert
        with self.assertRaisesRegexp(Exception,
                                     '"Inbound Ports" attribute must be empty when "Add Public IP" is false'):
            self.deploy_operation._validate_deployment_model(vm_deployment_model=deployment_model,
                                                             os_type=os_type,
                                                             network_actions=network_actions)

    def test_validate_deployment_model_has_extension_script_file(self):
        # Arrange
        deployment_model = Mock()
        deployment_model.extension_script_file = "http://bla.com/script"
        os_type = Mock()
        self.deploy_operation.vm_extension_service.validate_script_extension = Mock()
        network_actions = []

        # Act
        self.deploy_operation._validate_deployment_model(vm_deployment_model=deployment_model,
                                                         os_type=os_type,
                                                         network_actions=network_actions)

        # Assert
        self.deploy_operation.vm_extension_service.validate_script_extension.assert_called_once_with(
            image_os_type=os_type,
            script_file=deployment_model.extension_script_file,
            script_configurations=deployment_model.extension_script_configurations)

    def test_prepare_deployed_app_attributes(self):
        user = 'admin'
        password = 'pass'
        ip = '5.5.5.5'

        expected_res = [Attribute('Password', password),
                        Attribute('User', user),
                        Attribute('Public IP', ip)]

        res = self.deploy_operation._prepare_deployed_app_attributes(admin_username='admin',
                                                                     admin_password='pass',
                                                                     public_ip='5.5.5.5')

        self.assertEquals(value_for(res, 'User'), value_for(expected_res, 'User'))
        self.assertEquals(value_for(res, 'Password'), value_for(expected_res, 'Password'))
        self.assertEquals(value_for(res, 'Public IP'), value_for(expected_res, 'Public IP'))
        self.assertEquals(len(res), len(expected_res))


def value_for(attributes, attribute_name):
    return next(attribute.attributeValue for attribute in iter(attributes) if attribute.attributeName == attribute_name)
