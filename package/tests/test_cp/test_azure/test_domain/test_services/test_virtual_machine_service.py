from unittest import TestCase

import mock
from mock import MagicMock

from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService


class TestVirtualMachineService(TestCase):
    def setUp(self):
        self.vm_service = VirtualMachineService()

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachine")
    def test__create_vm(self, virtual_machine_class):
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

        # Act
        self.vm_service._create_vm(compute_management_client=compute_management_client,
                                   region=region,
                                   group_name=group_name,
                                   vm_name=vm_name,
                                   hardware_profile=hardware_profile,
                                   network_profile=network_profile,
                                   os_profile=os_profile,
                                   storage_profile=storage_profile,
                                   tags=tags)

        # Verify
        compute_management_client.virtual_machines.create_or_update.assert_called_with(group_name, vm_name, vm)
        virtual_machine_class.assert_called_once_with(hardware_profile=hardware_profile,
                                                      location=region,
                                                      network_profile=network_profile,
                                                      os_profile=os_profile,
                                                      storage_profile=storage_profile,
                                                      tags=tags)

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.StorageProfile")
    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.NetworkProfile")
    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.HardwareProfile")
    def test_create_vm(self, hardware_profile_class, network_profile_class, storage_profile_class):
        """Check that method will prepare all required parameters and call _create_vm method"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_vm_name"
        region = "test_region"
        tags = MagicMock()
        self.vm_service._create_vm = MagicMock()
        os_profile = MagicMock()
        hardware_profile = MagicMock()
        network_profile = MagicMock()
        storage_profile = MagicMock()
        self.vm_service._prepare_os_profile = MagicMock(return_value=os_profile)
        hardware_profile_class.return_value = hardware_profile
        network_profile_class.return_value = network_profile
        storage_profile_class.return_value = storage_profile

        # Act
        self.vm_service.create_vm(compute_management_client=compute_management_client,
                                  image_offer=MagicMock(),
                                  image_publisher=MagicMock(),
                                  image_sku=MagicMock(),
                                  image_version=MagicMock(),
                                  vm_credentials=MagicMock(),
                                  computer_name=MagicMock(),
                                  group_name=group_name,
                                  nic_id=MagicMock(),
                                  region=region,
                                  storage_name=MagicMock(),
                                  vm_name=vm_name,
                                  tags=tags,
                                  instance_type=MagicMock())

        # Verify
        self.vm_service._create_vm.assert_called_once_with(compute_management_client=compute_management_client,
                                                           group_name=group_name,
                                                           hardware_profile=hardware_profile,
                                                           network_profile=network_profile,
                                                           os_profile=os_profile,
                                                           region=region,
                                                           storage_profile=storage_profile,
                                                           tags=tags,
                                                           vm_name=vm_name)

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.StorageProfile")
    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.NetworkProfile")
    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.HardwareProfile")
    def test_create_vm_from_custom_image(self, hardware_profile_class, network_profile_class, storage_profile_class):
        """Check that method will prepare all required parameters and call _create_vm method"""
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_vm_name"
        region = "test_region"
        image_urn = "https://teststorage.blob.core.windows.net/testcontainer/testblob"
        tags = MagicMock()
        self.vm_service._create_vm = MagicMock()
        os_profile = MagicMock()
        hardware_profile = MagicMock()
        network_profile = MagicMock()
        storage_profile = MagicMock()
        self.vm_service._prepare_os_profile = MagicMock(return_value=os_profile)
        hardware_profile_class.return_value = hardware_profile
        network_profile_class.return_value = network_profile
        storage_profile_class.return_value = storage_profile

        # Act
        self.vm_service.create_vm_from_custom_image(compute_management_client=compute_management_client,
                                                    image_urn=image_urn,
                                                    image_os_type="Linux",
                                                    vm_credentials=MagicMock(),
                                                    computer_name=MagicMock(),
                                                    group_name=group_name,
                                                    nic_id=MagicMock(),
                                                    region=region,
                                                    storage_name=MagicMock(),
                                                    vm_name=vm_name,
                                                    tags=tags,
                                                    instance_type=MagicMock())

        # Verify
        self.vm_service._create_vm.assert_called_once_with(compute_management_client=compute_management_client,
                                                           group_name=group_name,
                                                           hardware_profile=hardware_profile,
                                                           network_profile=network_profile,
                                                           os_profile=os_profile,
                                                           region=region,
                                                           storage_profile=storage_profile,
                                                           tags=tags,
                                                           vm_name=vm_name)

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
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        res = self.vm_service.stop_vm(compute_management_client, group_name, vm_name)

        compute_management_client.virtual_machines.power_off.assert_called_with(resource_group_name=group_name,
                                                                                vm_name=vm_name)

        self.assertEqual(res, compute_management_client.virtual_machines.power_off().result())

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

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.LinuxConfiguration")
    def test_prepare_linux_configuration(self, linux_configuration_class):
        """Check that method will return LinuxConfiguration instance for the Azure client"""
        ssh_key = mock.MagicMock()
        linux_configuration = mock.MagicMock()
        linux_configuration_class.return_value = linux_configuration

        res = self.vm_service._prepare_linux_configuration(ssh_key)

        self.assertIs(res, linux_configuration)

    def test_get_image_operation_system(self):
        """Check that method returns operating_system of the provided image"""
        compute_client = mock.MagicMock()
        image = mock.MagicMock()
        compute_client.virtual_machine_images.get.return_value = image

        os_type = self.vm_service.get_image_operation_system(
                compute_management_client=compute_client,
                location=mock.MagicMock(),
                publisher_name=mock.MagicMock(),
                offer=mock.MagicMock(),
                skus=mock.MagicMock())

        compute_client.virtual_machine_images.list.assert_called_once()
        compute_client.virtual_machine_images.get.assert_called_once()
        self.assertEqual(os_type, image.os_disk_image.operating_system)

    def test_get_active_vm(self):
        """Check that method will return Azure VM if instance exists and is in "Succeeded" provisioning state"""
        vm_name = "test_vm_name"
        group_name = "test_group_name"
        compute_client = mock.MagicMock()
        mocked_vm = mock.MagicMock(provisioning_state=self.vm_service.SUCCEEDED_PROVISIONING_STATE)
        self.vm_service.get_vm = mock.MagicMock(return_value=mocked_vm)

        # Act
        vm = self.vm_service.get_active_vm(compute_management_client=compute_client, group_name=group_name,
                                           vm_name=vm_name)

        # Verify
        self.assertIs(vm, mocked_vm)

    def test_get_active_vm_raises_exception(self):
        """Check that method will raise exception if VM is not in "Succeeded" provisioning state"""
        vm_name = "test_vm_name"
        group_name = "test_group_name"
        compute_client = mock.MagicMock()
        mocked_vm = mock.MagicMock(provisioning_state="SOME_PROVISION_STATE")
        self.vm_service.get_vm = mock.MagicMock(return_value=mocked_vm)

        with self.assertRaises(Exception):
            self.vm_service.get_active_vm(compute_management_client=compute_client, group_name=group_name,
                                          vm_name=vm_name)

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.OperatingSystemTypes")
    def test_prepare_image_os_type_returns_linux(self, operating_system_types):
        """Check that method will return Linux OS type"""
        image_os_type = "Linux"

        # Act
        res = self.vm_service._prepare_image_os_type(image_os_type=image_os_type)

        # Verify
        self.assertEqual(res, operating_system_types.linux)

    @mock.patch("cloudshell.cp.azure.domain.services.virtual_machine_service.OperatingSystemTypes")
    def test_prepare_image_os_type_returns_windows(self, operating_system_types):
        """Check that method will return Windows OS type"""
        image_os_type = "Windows"

        # Act
        res = self.vm_service._prepare_image_os_type(image_os_type=image_os_type)

        # Verify
        self.assertEqual(res, operating_system_types.windows)
