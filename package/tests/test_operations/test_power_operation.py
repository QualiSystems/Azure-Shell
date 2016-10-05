from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.vm_management.operations.power_operation import PowerAzureVMOperation


class TestPowerAzureVMOperation(TestCase):
    def setUp(self):
        self.logger = mock.MagicMock()
        self.vm_service = mock.MagicMock()
        self.compute_client = mock.MagicMock()
        self.resource_group_name = "test_group_name"
        self.vm_name = "test_vm_name"
        self.power_operation = PowerAzureVMOperation(logger=self.logger, vm_service=self.vm_service)

    def test_power_on(self):
        self.power_operation.power_on(self.compute_client, self.resource_group_name, self.vm_name)
        self.vm_service.start_vm.assert_called_once_with(self.compute_client, self.resource_group_name, self.vm_name)

    def test_power_off(self):
        self.power_operation.power_off(self.compute_client, self.resource_group_name, self.vm_name)
        self.vm_service.stop_vm.assert_called_once_with(self.compute_client, self.resource_group_name, self.vm_name)
