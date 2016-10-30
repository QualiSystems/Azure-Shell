from unittest import TestCase
from mock import Mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.delete_operation import DeleteAzureVMOperation
from tests.helpers.test_helper import TestHelper


class TestDeleteOperation(TestCase):
    def setUp(self):
        self.logger = Mock()
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.delete_operation = DeleteAzureVMOperation(logger=self.logger,
                                                       vm_service=self.vm_service,
                                                       network_service=self.network_service)

    def test_delete_operation(self):
        """
        :return:
        """

        # Arrange
        self.vm_service.delete_vm = Mock()
        self.network_service.delete_nic = Mock()
        self.network_service.delete_ip = Mock()

        # Act
        self.delete_operation.delete(compute_client=Mock(),
                                     network_client=Mock(),
                                     group_name="AzureTestGroup",
                                     vm_name="AzureTestVM"
                                     )

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.delete_vm))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.network_service.delete_nic))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.network_service.delete_ip))

    def test_delete_operation_on_error(self):
        # Arrange
        self.vm_service.delete_vm = Mock(side_effect=Exception("Boom!"))

        # Act
        self.assertRaises(Exception,
                          self.delete_operation.delete,
                          Mock(),
                          Mock(),
                          "AzureTestGroup",
                          "AzureTestVM")

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.logger.info))

    def test_delete_resource_group_operation_on_error(self):
        # Arrange
        self.vm_service.delete_resource_group = Mock(side_effect=Exception("Boom!"))

        # Act
        self.assertRaises(Exception,
                          self.delete_operation.delete_resource_group,
                          Mock(),
                          "group_name_test")
