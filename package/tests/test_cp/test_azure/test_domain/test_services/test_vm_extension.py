# -*- coding: utf-8 -*-
from unittest import TestCase

import mock

from cloudshell.cp.azure.common.helpers.url_helper import URLHelper
from cloudshell.cp.azure.domain.services.vm_extension import VMExtensionService


class UrlHelperMock(URLHelper):
    def check_url(self, url):
        return True


class TestVMExtensionService(TestCase):
    def setUp(self):
        self.location = "southcentralus"
        self.script_file = "https://gist.github.com/ahmetalpbalkan/raw/40507c990a4d5a2f5c79f901fa89a80841/hello.sh"
        self.script_configurations = ""
        self.vm_extension_service = VMExtensionService(url_helper=UrlHelperMock(),waiter_service=mock.MagicMock())
        self.tags = mock.MagicMock()

    @mock.patch("cloudshell.cp.azure.domain.services.vm_extension.OperatingSystemTypes")
    def test_validate_script_extension_checks_windows_powershell_format(self, operating_system_types):
        """Check that method will raise exception if OS is Windows and scripts extension is not .ps1"""
        with self.assertRaises(Exception):
            self.vm_extension_service.validate_script_extension(image_os_type=operating_system_types.windows,
                                                                script_file=self.script_file,
                                                                script_configurations=self.script_file)

    @mock.patch("cloudshell.cp.azure.domain.services.vm_extension.OperatingSystemTypes")
    def test_validate_script_extension_checks_linux_script_configurations_is_not_empty(self, operating_system_types):
        """Check that method will raise exception if OS is Linux and script_configurations is empty"""
        with self.assertRaises(Exception):
            self.vm_extension_service.validate_script_extension(image_os_type=operating_system_types.linux,
                                                                script_file=self.script_file,
                                                                script_configurations="")

    @mock.patch("cloudshell.cp.azure.domain.services.vm_extension.VirtualMachineExtension")
    def test_prepare_linux_vm_script_extension(self, virtual_machine_extension_class):
        """Check that method will return VirtualMachineExtension model"""
        virtual_machine_extension = mock.MagicMock()
        virtual_machine_extension_class.return_value = virtual_machine_extension

        # Act
        result = self.vm_extension_service._prepare_linux_vm_script_extension(
            location=self.location,
            script_file=self.script_file,
            script_configurations=self.script_configurations,
            tags=self.tags)

        # Verify
        self.assertEqual(result, virtual_machine_extension)
        virtual_machine_extension_class.assert_called_once_with(
            location=self.location,
            publisher=self.vm_extension_service.LINUX_PUBLISHER,
            tags=self.tags,
            type_handler_version=self.vm_extension_service.LINUX_HANDLER_VERSION,
            virtual_machine_extension_type=self.vm_extension_service.LINUX_EXTENSION_TYPE,
            settings={
                "fileUris": [self.script_file],
                "commandToExecute": self.script_configurations
            })

    @mock.patch("cloudshell.cp.azure.domain.services.vm_extension.VirtualMachineExtension")
    def test_prepare_windows_vm_script_extension(self, virtual_machine_extension_class):
        """Check that method will return VirtualMachineExtension model"""
        virtual_machine_extension = mock.MagicMock()
        virtual_machine_extension_class.return_value = virtual_machine_extension
        file_name = "test_script.ps1"
        script_file = "https://gist.github.com/ahmetalpbalkan/raw/40507c9905a2f5c79f901fa89a80841/{}".format(file_name)

        # Act
        result = self.vm_extension_service._prepare_windows_vm_script_extension(
            location=self.location,
            script_file=script_file,
            script_configurations=self.script_configurations,
            tags=self.tags)

        # Verify
        self.assertEqual(result, virtual_machine_extension)
        virtual_machine_extension_class.assert_called_once_with(
            location=self.location,
            publisher=self.vm_extension_service.WINDOWS_PUBLISHER,
            tags=self.tags,
            type_handler_version=self.vm_extension_service.WINDOWS_HANDLER_VERSION,
            virtual_machine_extension_type=self.vm_extension_service.WINDOWS_EXTENSION_TYPE,
            settings={
                "fileUris": [script_file],
                "commandToExecute": "powershell.exe -ExecutionPolicy Unrestricted -File {} ".format(file_name)
            })

    @mock.patch("cloudshell.cp.azure.domain.services.vm_extension.OperatingSystemTypes")
    def test_create_script_extension_for_windows_os(self, operating_system_types):
        """Check that method will use compute_client to create Windows script extension"""
        compute_client = mock.MagicMock()
        vm_extension_model = mock.MagicMock()
        group_name = "testgroupname"
        vm_name = "testvmname"
        self.vm_extension_service._prepare_windows_vm_script_extension = mock.MagicMock(
            return_value=vm_extension_model)

        # Act
        self.vm_extension_service.create_script_extension(
            compute_client=compute_client,
            location=self.location,
            group_name=group_name,
            vm_name=vm_name,
            image_os_type=operating_system_types.windows,
            script_file=self.script_file,
            script_configurations=self.script_configurations,
            tags=self.tags)

        # Verify
        compute_client.virtual_machine_extensions.create_or_update.assert_called_once_with(
            extension_parameters=vm_extension_model,
            resource_group_name=group_name,
            vm_extension_name=vm_name,
            vm_name=vm_name)

    @mock.patch("cloudshell.cp.azure.domain.services.vm_extension.OperatingSystemTypes")
    def test_create_script_extension_for_linux_os(self, operating_system_types):
        """Check that method will use compute_client to create Linux script extension"""
        compute_client = mock.MagicMock()
        vm_extension_model = mock.MagicMock()
        group_name = "testgroupname"
        vm_name = "testvmname"
        self.vm_extension_service._prepare_linux_vm_script_extension = mock.MagicMock(
            return_value=vm_extension_model)

        # Act
        self.vm_extension_service.create_script_extension(
            compute_client=compute_client,
            location=self.location,
            group_name=group_name,
            vm_name=vm_name,
            image_os_type=operating_system_types.linux,
            script_file=self.script_file,
            script_configurations=self.script_configurations,
            tags=self.tags)

        # Verify
        compute_client.virtual_machine_extensions.create_or_update.assert_called_once_with(
            extension_parameters=vm_extension_model,
            resource_group_name=group_name,
            vm_extension_name=vm_name,
            vm_name=vm_name)

    def test_url_helper(self):
        uh = URLHelper()

        self.assertTrue(uh.check_url('http://www.google.com'))
        self.assertFalse(uh.check_url('https://en.wikipedia.org/wiki/List_of_HTTP_status_codesqqdfdfqqq'))
        self.assertFalse(uh.check_url('‪C:\\QsPythonDriverHost.log'))
        self.assertFalse(uh.check_url(u'https://gist.github.com/ahmetalpbalkan/b5d4a856fe15464015ae87d5587a4439/raw/466f5c30507c990a4d5a2f5c79f901fa89a80841/hello.shha'))
