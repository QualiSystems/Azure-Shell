from unittest import TestCase
from mock import Mock, MagicMock
from msrestazure.azure_exceptions import CloudError
from requests import Response

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.security_group import SecurityGroupService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.delete_operation import DeleteAzureVMOperation
from tests.helpers.test_helper import TestHelper


class TestDeleteOperation(TestCase):
    def setUp(self):
        self.logger = Mock()
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.tags_service = TagService()
        self.security_group_service = SecurityGroupService(self.network_service)
        self.delete_operation = DeleteAzureVMOperation(vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       tags_service=self.tags_service,
                                                       security_group_service=self.security_group_service)

    def test_delete_operation(self):
        """
        :return:
        """

        # Arrange
        self.vm_service.delete_vm = Mock()
        network_client = Mock()
        network_client.network_interfaces.delete = Mock()
        network_client.public_ip_addresses.delete = Mock()
        self.delete_operation.security_group_service.delete_security_rules = Mock()

        # Act
        self.delete_operation.delete(compute_client=Mock(),
                                     network_client=network_client,
                                     group_name="AzureTestGroup",
                                     vm_name="AzureTestVM",
                                     logger=self.logger)

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.delete_vm))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(network_client.public_ip_addresses.delete))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(network_client.network_interfaces.delete))

    def test_delete_operation_on_error(self):
        # Arrange
        self.vm_service.delete_vm = Mock(side_effect=Exception("Boom!"))

        # Act
        self.assertRaises(Exception,
                          self.delete_operation.delete,
                          Mock(),
                          Mock(),
                          "AzureTestGroup",
                          "AzureTestVM",
                          self.logger)

        # Verify
        self.logger.exception.assert_called()

    def test_delete_operation_on_cloud_error_not_found_no_exception(self):
        # Arrange
        response = Response()
        response.status_code = 0
        response.reason = "Not Found"
        error = CloudError(response)
        self.vm_service.delete_vm = Mock(side_effect=error)
        self.delete_operation.security_group_service.delete_security_rules = Mock()

        # Act
        self.delete_operation.delete(
            Mock(),
            Mock(),
            "group_name",
            "vm_name",
            self.logger)

        # Verify
        self.logger.info.assert_called()

    def test_delete_operation_on_cloud_any_error_throws_exception(self):
        # Arrange
        response = Response()
        response.status_code = 0
        response.reason = "Bla bla error"
        error = CloudError(response)
        self.vm_service.delete_vm = Mock(side_effect=error)

        # Act
        self.assertRaises(Exception,
                          self.delete_operation.delete,
                          Mock(),
                          Mock(),
                          "AzureTestGroup",
                          "AzureTestVM")

    def test_delete_resource_group_operation_on_error(self):
        # Arrange
        self.vm_service.delete_resource_group = Mock(side_effect=Exception("Boom!"))

        # Act
        self.assertRaises(Exception,
                          self.delete_operation.delete_resource_group,
                          Mock(),
                          "group_name_test")

    def test_delete_resource_group(self):
        # Arrange
        resource_management_client = Mock()
        group_name = "test_group_name"

        # Act
        self.vm_service.delete_resource_group(resource_management_client, group_name)

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(resource_management_client.resource_groups.delete))
        resource_management_client.resource_groups.delete.assert_called_with(group_name)

    def test_delete_vm(self):
        # Arrange
        compute_management_client = MagicMock()
        group_name = "test_group_name"
        vm_name = "test_group_name"

        # Act
        res = self.vm_service.delete_vm(compute_management_client, group_name, vm_name)

        # Verify
        compute_management_client.virtual_machines.delete.assert_called_with(resource_group_name=group_name,
                                                                             vm_name=vm_name)
