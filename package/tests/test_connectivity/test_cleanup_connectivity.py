from unittest import TestCase

from mock import Mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.delete_operation import DeleteAzureVMOperation
from helpers.test_helper import TestHelper


class TestCleanupConnectivity(TestCase):
    def setUp(self):
        self.logger = Mock()
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.delete_operation = DeleteAzureVMOperation(logger=self.logger,
                                                       vm_service=self.vm_service,
                                                       network_service=self.network_service)

    def test_cleanup(self):
        """
        :return:
        """

        # Arrange
        self.vm_service.delete_resource_group = Mock()

        # Act
        self.delete_operation.delete_resource_group(resource_client=Mock(),group_name=Mock())

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.delete_resource_group))
