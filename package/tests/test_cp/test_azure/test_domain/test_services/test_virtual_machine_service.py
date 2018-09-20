from unittest import TestCase

from azure.mgmt.compute.models import Plan, DiskCreateOptionTypes, OSDisk, ManagedDiskParameters, StorageAccountTypes, \
    ImageReference, NetworkInterfaceReference
from mock import MagicMock, Mock, patch
from msrestazure.azure_exceptions import CloudError

from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService


class TestVirtualMachineService(TestCase):
    def setUp(self):
        self.vm_service = VirtualMachineService(MagicMock())

    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.BootDiagnostics")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.DiagnosticsProfile")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachine")
    def test__create_vm(self, virtual_machine_class, diagnostics_profile_class, boot_diag_class):
        """Check that method will create VirtualMachine instance and execute create_or_update request"""
        compute_management_client = MagicMock()
        region = "test_region"
        group_name = "test_group_name"
        vm_name = "test_vm_name"
        hardware_profile = MagicMock()
        network_profile = MagicMock()
        os_profile = MagicMock()
        storage_profile = MagicMock()
        tags = MagicMock()
        vm = MagicMock()
        virtual_machine_class.return_value = vm
        plan = MagicMock()
        cancellation_context = MagicMock()
        boot_diag = MagicMock()
        boot_diag_class.return_value = boot_diag
        diagnostics_profile = MagicMock()
        diagnostics_profile_class.return_value = diagnostics_profile

        # Act
        self.vm_service._create_vm(compute_management_client=compute_management_client,
                                   region=region,
                                   group_name=group_name,
                                   vm_name=vm_name,
                                   hardware_profile=hardware_profile,
                                   network_profile=network_profile,
                                   os_profile=os_profile,
                                   storage_profile=storage_profile,
                                   cancellation_context=cancellation_context,
                                   tags=tags,
                                   vm_plan=plan)

        # Verify
        boot_diag_class.assert_called_once_with(enabled=False)
        compute_management_client.virtual_machines.create_or_update.assert_called_with(group_name, vm_name, vm)
        virtual_machine_class.assert_called_once_with(location=region,
                                                      tags=tags,
                                                      hardware_profile=hardware_profile,
                                                      network_profile=network_profile,
                                                      os_profile=os_profile,
                                                      storage_profile=storage_profile,
                                                      diagnostics_profile=diagnostics_profile,
                                                      plan=plan)

    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.StorageProfile")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.NetworkProfile")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.HardwareProfile")
    def test_create_vm(self, hardware_profile_class, network_profile_class, storage_profile_class):
        """Check that method will prepare all required parameters and call _create_vm method"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_vm_name"
        region = "test_region"
        tags = MagicMock()
        cancellation_context = MagicMock()
        self.vm_service._create_vm = MagicMock()
        os_profile = MagicMock()
        hardware_profile = MagicMock()
        network_profile = MagicMock()
        storage_profile = MagicMock()
        self.vm_service._prepare_os_profile = MagicMock(return_value=os_profile)
        hardware_profile_class.return_value = hardware_profile
        network_profile_class.return_value = network_profile
        storage_profile_class.return_value = storage_profile
        image_sku = MagicMock()
        image_offer = MagicMock()
        image_publisher = MagicMock()
        disk_type = Mock()
        disk_size = "40"
        nics = [NetworkInterfaceReference(id=Mock(), primary=True)]

        plan = Plan(name=image_sku, publisher=image_publisher, product=image_offer)

        # Act
        self.vm_service.create_vm_from_marketplace(compute_management_client=compute_management_client,
                                                   image_offer=image_offer,
                                                   image_publisher=image_publisher,
                                                   image_sku=image_sku,
                                                   image_version=MagicMock(),
                                                   disk_type=disk_type,
                                                   disk_size=disk_size,
                                                   nics=nics,
                                                   vm_credentials=MagicMock(),
                                                   computer_name=MagicMock(),
                                                   group_name=group_name,
                                                   region=region,
                                                   vm_name=vm_name,
                                                   tags=tags,
                                                   vm_size=MagicMock(),
                                                   purchase_plan=plan,
                                                   cancellation_context=cancellation_context)

        # Verify
        self.vm_service._create_vm.assert_called_once_with(compute_management_client=compute_management_client,
                                                           group_name=group_name,
                                                           hardware_profile=hardware_profile,
                                                           network_profile=network_profile,
                                                           os_profile=os_profile,
                                                           region=region,
                                                           storage_profile=storage_profile,
                                                           tags=tags,
                                                           vm_name=vm_name,
                                                           vm_plan=plan,
                                                           cancellation_context=cancellation_context)

    def test_get_storage_type_premium(self):
        # Arrange
        disk_type = "SSD"

        # Act
        storage_type = self.vm_service._get_storage_type(disk_type=disk_type)

        # Assert
        self.assertEquals(storage_type, StorageAccountTypes.premium_lrs)

    def test_get_storage_type_standard(self):
        # Arrange
        disk_type = "HDD"

        # Act
        storage_type = self.vm_service._get_storage_type(disk_type=disk_type)

        # Assert
        self.assertEquals(storage_type, StorageAccountTypes.standard_lrs)

    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.OSDisk")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.ManagedDiskParameters")
    def test_prepare_os_disk(self, managed_disk_parameters_class, os_disk_class):
        # Arrange
        disk_type = "SSD"
        disk_size = "40"
        managed_disk_parameters = Mock()
        managed_disk_parameters_class.return_value = managed_disk_parameters
        os_disk = Mock()
        os_disk_class.return_value = os_disk
        storage_type = Mock()
        self.vm_service._get_storage_type = Mock(return_value=storage_type)

        # Act
        os_disk = self.vm_service._prepare_os_disk(disk_type=disk_type, disk_size=disk_size)

        # Assert
        self.vm_service._get_storage_type.assert_called_once_with(disk_type)
        managed_disk_parameters_class.assert_called_once_with(storage_account_type=storage_type)
        os_disk_class.assert_called_once_with(create_option=DiskCreateOptionTypes.from_image,
                                              managed_disk=managed_disk_parameters,
                                              disk_size_gb=int(disk_size))

    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.NetworkInterfaceReference")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.ImageReference")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.StorageProfile")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.NetworkProfile")
    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.HardwareProfile")
    def test_create_vm_from_custom_image(self, hardware_profile_class, network_profile_class, storage_profile_class,
                                         image_reference_class, network_interface_class):
        """Check that method will prepare all required parameters and call _create_vm method"""
        image_mock = Mock()
        image_mock.id = "id"
        compute_management_client = Mock()
        compute_management_client.images.get = Mock(return_value=image_mock)

        group_name = "test_group_name"
        vm_name = "test_vm_name"
        region = "test_region"
        image_name = "image_name"
        image_resource_group = "image_resource_group"
        nic_id = "nic_id"
        vm_size = "vm_size"
        tags = MagicMock()
        disk_type = "SSD"
        disk_size = "40"

        cancellation_context = MagicMock()

        os_profile = MagicMock()
        os_disk = Mock()
        self.vm_service._create_vm = MagicMock()
        self.vm_service._prepare_os_profile = Mock(return_value=os_profile)
        self.vm_service._prepare_os_disk = Mock(return_value=os_disk)

        network_profile = Mock()
        network_profile_class.return_value = network_profile
        hardware_profile = Mock()
        hardware_profile_class.return_value = hardware_profile
        storage_profile = Mock()
        storage_profile_class.return_value = storage_profile
        image_reference = Mock()
        image_reference_class.return_value = image_reference
        network_interface = Mock()
        network_interface_class.return_value = network_interface
        nics = [NetworkInterfaceReference(id='5')]
        logger = Mock()

        # Act
        self.vm_service.create_vm_from_custom_image(compute_management_client=compute_management_client,
                                                    image_name=image_name,
                                                    image_resource_group=image_resource_group,
                                                    disk_type=disk_type,
                                                    vm_credentials=MagicMock(),
                                                    computer_name=MagicMock(),
                                                    group_name=group_name,
                                                    region=region,
                                                    vm_name=vm_name,
                                                    tags=tags,
                                                    vm_size=vm_size,
                                                    cancellation_context=cancellation_context,
                                                    disk_size=disk_size,
                                                    nics=nics,
                                                    logger=logger)

        # Verify
        hardware_profile_class.assert_called_once_with(vm_size=vm_size)
        network_interface_class.assert_called_once_with(id='5')
        network_profile_class.assert_called_once_with(network_interfaces=[network_interface])
        compute_management_client.images.get.assert_called_once_with(resource_group_name=image_resource_group,
                                                                     image_name=image_name)
        image_reference_class.assert_called_once_with(id=image_mock.id)
        self.vm_service._prepare_os_disk.assert_called_once_with(disk_type, disk_size)
        storage_profile_class.assert_called_once_with(
            os_disk=os_disk,
            image_reference=image_reference)
        self.vm_service._create_vm.assert_called_once_with(compute_management_client=compute_management_client,
                                                           group_name=group_name,
                                                           hardware_profile=hardware_profile,
                                                           network_profile=network_profile,
                                                           os_profile=os_profile,
                                                           region=region,
                                                           storage_profile=storage_profile,
                                                           cancellation_context=cancellation_context,
                                                           tags=tags,
                                                           vm_name=vm_name,
                                                           logger=logger)

    def test_vm_service_create_resource_group(self):
        # Arrange
        resource_management_client = MagicMock()
        resource_management_client.resource_groups.create_or_update = MagicMock(return_value="A test group")

        # Act
        region = 'region'
        group_name = MagicMock()
        tags = {}
        self.vm_service.create_resource_group(resource_management_client=resource_management_client,
                                              region=region,
                                              group_name=group_name, tags=tags)

        # Verify
        from azure.mgmt.resource.resources.models import ResourceGroup
        resource_management_client.resource_groups.create_or_update(group_name,
                                                                    ResourceGroup(location=region, tags=tags))

    def test_start_vm(self):
        """Check that method calls azure client to start VM action and returns it result"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        res = self.vm_service.start_vm(compute_management_client, group_name, vm_name)

        compute_management_client.virtual_machines.start.assert_called_with(resource_group_name=group_name,
                                                                            vm_name=vm_name)

        self.assertEqual(res, compute_management_client.virtual_machines.start().result())

    def test_stop_vm(self):
        """Check that method calls azure client to stop VM action and returns it result"""
        # arrange
        compute_management_client = Mock()
        compute_management_client.virtual_machines = Mock()
        vm_deallocate_mock = Mock()
        vm_deallocate_mock.wait = Mock()
        compute_management_client.virtual_machines.deallocate = Mock(return_value=vm_deallocate_mock)
        group_name = "test_group_name"
        vm_name = "test_group_name"

        # act
        self.vm_service.stop_vm(compute_management_client, group_name, vm_name, False)

        # assert
        compute_management_client.virtual_machines.deallocate.assert_called_once_with(resource_group_name=group_name,
                                                                                      vm_name=vm_name)
        vm_deallocate_mock.wait.assert_called_once()

    def test_start_vm_with_async_mode_true(self):
        """Check that method calls azure client to start VM action and doesn't wait for it result"""
        compute_management_client = MagicMock()
        operation_poller = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"
        compute_management_client.virtual_machines.power_off.return_value = operation_poller

        res = self.vm_service.start_vm(compute_management_client, group_name, vm_name, async=True)

        operation_poller.result.assert_not_called()
        self.assertIsNone(res)

    def test_stop_vm_with_async_mode_true(self):
        """Check that method calls azure client to stop VM action and doesn't wait for it result"""
        compute_management_client = MagicMock()
        operation_poller = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"
        compute_management_client.virtual_machines.power_off.return_value = operation_poller

        res = self.vm_service.stop_vm(compute_management_client, group_name, vm_name, async=True)

        operation_poller.result.assert_not_called()
        self.assertIsNone(res)

    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.LinuxConfiguration")
    def test_prepare_linux_configuration(self, linux_configuration_class):
        """Check that method will return LinuxConfiguration instance for the Azure client"""
        ssh_key = MagicMock()
        linux_configuration = MagicMock()
        linux_configuration_class.return_value = linux_configuration

        res = self.vm_service._prepare_linux_configuration(ssh_key)

        self.assertIs(res, linux_configuration)

    def test_get_virtual_machine_image(self):
        """Check that method returns operating_system of the provided image"""
        compute_client = MagicMock()
        image = MagicMock()
        compute_client.virtual_machine_images.get.return_value = image

        vm_image = self.vm_service.get_virtual_machine_image(
            compute_management_client=compute_client,
            location=MagicMock(),
            publisher_name=MagicMock(),
            offer=MagicMock(),
            skus=MagicMock())

        compute_client.virtual_machine_images.list.assert_called_once()
        compute_client.virtual_machine_images.get.assert_called_once()
        self.assertEqual(vm_image.os_disk_image.operating_system, image.os_disk_image.operating_system)

    def test_get_active_vm(self):
        """Check that method will return Azure VM if instance exists and is in "Succeeded" provisioning state"""
        vm_name = "test_vm_name"
        group_name = "test_group_name"
        compute_client = MagicMock()
        mocked_vm = MagicMock(provisioning_state=self.vm_service.SUCCEEDED_PROVISIONING_STATE)
        self.vm_service.get_vm = MagicMock(return_value=mocked_vm)

        # Act
        vm = self.vm_service.get_active_vm(compute_management_client=compute_client, group_name=group_name,
                                           vm_name=vm_name)

        # Verify
        self.assertIs(vm, mocked_vm)

    def test_get_active_vm_raises_exception(self):
        """Check that method will raise exception if VM is not in "Succeeded" provisioning state"""
        vm_name = "test_vm_name"
        group_name = "test_group_name"
        compute_client = MagicMock()
        mocked_vm = MagicMock(provisioning_state="SOME_PROVISION_STATE")
        self.vm_service.get_vm = MagicMock(return_value=mocked_vm)

        with self.assertRaises(Exception):
            self.vm_service.get_active_vm(compute_management_client=compute_client, group_name=group_name,
                                          vm_name=vm_name)

    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.OperatingSystemTypes")
    def test_prepare_image_os_type_returns_linux(self, operating_system_types):
        """Check that method will return Linux OS type"""
        image_os_type = "Linux"

        # Act
        res = self.vm_service.prepare_image_os_type(image_os_type=image_os_type)

        # Verify
        self.assertEqual(res, operating_system_types.linux)

    @patch("cloudshell.cp.azure.domain.services.virtual_machine_service.OperatingSystemTypes")
    def test_prepare_image_os_type_returns_windows(self, operating_system_types):
        """Check that method will return Windows OS type"""
        image_os_type = "Windows"

        # Act
        res = self.vm_service.prepare_image_os_type(image_os_type=image_os_type)

        # Verify
        self.assertEqual(res, operating_system_types.windows)

    def test_get_resource_group(self):
        """Check that method will use resource_client to find needed resource group"""
        resource_client = MagicMock()
        group_name = "test_group_name"
        expected_resource_group = MagicMock()
        resource_client.resource_groups.get.return_value = expected_resource_group

        # Act
        result = self.vm_service.get_resource_group(resource_management_client=resource_client, group_name=group_name)

        # Verify
        resource_client.resource_groups.get.assert_called_once_with(resource_group_name=group_name)
        self.assertEqual(result, expected_resource_group)

    def test_list_virtual_machine_sizes(self):
        """Check that method will use compute_client to find list VM sizes"""
        compute_client = MagicMock()
        location = "test_location"
        expected_vm_sizes = MagicMock()
        compute_client.virtual_machine_sizes.list.return_value = expected_vm_sizes

        # Act
        result = self.vm_service.list_virtual_machine_sizes(compute_management_client=compute_client,
                                                            location=location)

        # Verify
        compute_client.virtual_machine_sizes.list.assert_called_once_with(location=location)
        self.assertEqual(result, expected_vm_sizes)

    def test_prepare_os_profile_with_accesskey(self):
        # Arrange
        computer_name = "name"
        vm_credentials = Mock()
        vm_credentials.ssh_key = "key"
        vm_credentials.admin_username = "admin_user"

        linux_configuration = Mock()
        self.vm_service._prepare_linux_configuration = Mock(return_value=linux_configuration)

        # Act
        os_profile = self.vm_service._prepare_os_profile(vm_credentials=vm_credentials, computer_name=computer_name)

        # Assert
        self.vm_service._prepare_linux_configuration.assert_called_once_with(vm_credentials.ssh_key)
        self.assertEquals(os_profile.admin_username, vm_credentials.admin_username)
        self.assertEquals(os_profile.admin_password, vm_credentials.admin_password)
        self.assertEquals(os_profile.linux_configuration, linux_configuration)
        self.assertEquals(os_profile.computer_name, computer_name)

    def test_prepare_os_profile_no_accesskey(self):
        # Arrange
        computer_name = "name"
        vm_credentials = Mock()
        vm_credentials.ssh_key = None
        vm_credentials.admin_username = "admin_user"
        vm_credentials.admin_username = "pass"

        self.vm_service._prepare_linux_configuration = Mock()

        # Act
        os_profile = self.vm_service._prepare_os_profile(vm_credentials=vm_credentials, computer_name=computer_name)

        # Assert
        self.vm_service._prepare_linux_configuration.assert_not_called()
        self.assertEquals(os_profile.admin_username, vm_credentials.admin_username)
        self.assertEquals(os_profile.admin_password, vm_credentials.admin_password)
        self.assertEquals(os_profile.linux_configuration, None)
        self.assertEquals(os_profile.computer_name, computer_name)
