from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.vm_management.operations.power_operation import PowerAzureVMOperation


class TestPowerAzureVMOperation(TestCase):
    def setUp(self):
        self.vm_service = mock.MagicMock()
        self.data_holder = mock.MagicMock()
        self.cloudshell_session = mock.MagicMock()
        self.vm_custom_params_extractor = mock.MagicMock()
        self.compute_client = mock.MagicMock()
        self.resource_group_name = "test_group_name"
        self.resource_full_name = "test_resource_full_name"
        self.vm_name = "test_vm_name"
        self.power_operation = PowerAzureVMOperation(vm_service=self.vm_service,
                                                     vm_custom_params_extractor=self.vm_custom_params_extractor)

    def test_power_on(self):
        self.vm_custom_params_extractor.get_custom_param_value.return_value = False

        # Act
        self.power_operation.power_on(compute_client=self.compute_client,
                                      resource_group_name=self.resource_group_name,
                                      resource_full_name=self.resource_full_name,
                                      data_holder=self.data_holder,
                                      cloudshell_session=self.cloudshell_session)

        # Verify
        self.vm_service.start_vm.assert_called_once_with(self.compute_client,
                                                         self.resource_group_name,
                                                         self.data_holder.name)

    def test_power_off(self):
        self.power_operation.power_off(self.compute_client, self.resource_group_name, self.vm_name)
        self.vm_service.stop_vm.assert_called_once_with(self.compute_client, self.resource_group_name, self.vm_name)

    def test_power_on_when_extension_time_out_is_true(self):
        """Check that method will set "Error" live status for the VM and throw exception

        if VM extension installation fails"""
        self.vm_custom_params_extractor.get_custom_param_value.return_value = "True"

        with self.assertRaisesRegexp(Exception, "Partially deployed app: VM Custom Script Extension failed to compete "
                                                "within the specified timeout"):
            # Act
            self.power_operation.power_on(compute_client=self.compute_client,
                                          resource_group_name=self.resource_group_name,
                                          resource_full_name=self.resource_full_name,
                                          data_holder=self.data_holder,
                                          cloudshell_session=self.cloudshell_session)

        # Verify
        self.cloudshell_session.SetResourceLiveStatus.assert_called_once_with(
            self.resource_full_name,
            "Error",
            "Partially deployed app")
