from threading import Lock
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
        self.vm_service = VirtualMachineService(MagicMock())
        self.network_service = NetworkService(MagicMock(), MagicMock())
        self.tags_service = TagService()
        self.storage_service = MagicMock()
        self.security_group_service = SecurityGroupService(self.network_service)
        self.generic_lock_provider = Mock()
        self.generic_lock_provider.get_resource_lock = Mock(return_value=Mock())
        self.delete_operation = DeleteAzureVMOperation(vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       tags_service=self.tags_service,
                                                       security_group_service=self.security_group_service,
                                                       storage_service=self.storage_service,
                                                       generic_lock_provider=self.generic_lock_provider,
                                                       subnet_locker=Lock())

    def test_cleanup_on_error(self):
        # Arrange
        test_exception_message = "lalala"
        self.delete_operation.remove_nsg_from_subnet = Mock(side_effect=Exception(test_exception_message))
        self.delete_operation.delete_sandbox_subnet = Mock()

        # Act
        result = self.delete_operation.cleanup_connectivity(network_client=Mock(),
                                                            resource_client=Mock(),
                                                            cloud_provider_model=Mock(),
                                                            resource_group_name=Mock(),
                                                            logger=self.logger)

        # Verify
        self.assertFalse(result['success'])
        self.assertEqual(result['errorMessage'],
                         "CleanupConnectivity ended with the error(s): ['lalala']".format(test_exception_message))
        self.logger.exception.assert_called()

    def test_cleanup(self):
        """
        :return:
        """

        # Arrange
        self.delete_operation.remove_nsg_from_subnet = Mock()
        self.delete_operation.delete_resource_group = Mock()
        self.delete_operation.delete_sandbox_subnet = Mock()
        tested_group_name = "test_group"
        resource_client = Mock()
        network_client = Mock()
        cloud_provider_model = Mock()

        vnet = Mock()
        subnet = Mock()
        subnet.name = tested_group_name
        vnet.subnets = [subnet]
        reservation = Mock()
        reservation.reservation_id = tested_group_name
        self.network_service.get_sandbox_virtual_network = Mock(return_value=vnet)

        # Act
        self.delete_operation.cleanup_connectivity(network_client=network_client,
                                                   resource_client=resource_client,
                                                   cloud_provider_model=cloud_provider_model,
                                                   resource_group_name=tested_group_name,
                                                   logger=self.logger)

        # Verify
        self.delete_operation.remove_nsg_from_subnet.assert_called_once_with(network_client=network_client,
                                                                             cloud_provider_model=cloud_provider_model,
                                                                             resource_group_name=tested_group_name,
                                                                             logger=self.logger)

        self.delete_operation.delete_sandbox_subnet.assert_called_once_with(network_client=network_client,
                                                                            cloud_provider_model=cloud_provider_model,
                                                                            resource_group_name=tested_group_name,
                                                                            logger=self.logger)

        self.delete_operation.delete_resource_group.assert_called_once_with(resource_client=resource_client,
                                                                            group_name=tested_group_name,
                                                                            logger=self.logger)

        self.delete_operation.delete_resource_group.assert_called_with(resource_client=resource_client,
                                                                       logger=self.logger,
                                                                       group_name=tested_group_name)

    def test_cleanup(self):
        """
        :return:
        """

        # Arrange
        self.delete_operation.remove_nsg_from_subnet = Mock()
        self.delete_operation.delete_resource_group = Mock()
        self.delete_operation.delete_sandbox_subnet = Mock()
        tested_group_name = "test_group"
        resource_client = Mock()
        network_client = Mock()
        cloud_provider_model = Mock()

        vnet = Mock()
        subnet = Mock()
        subnet.name = tested_group_name
        vnet.subnets = [subnet]
        reservation = Mock()
        reservation.reservation_id = tested_group_name
        self.network_service.get_sandbox_virtual_network = Mock(return_value=vnet)

        # Act
        self.delete_operation.cleanup_connectivity(network_client=network_client,
                                                   resource_client=resource_client,
                                                   cloud_provider_model=cloud_provider_model,
                                                   resource_group_name=tested_group_name,
                                                   logger=self.logger)

        # Verify
        self.delete_operation.remove_nsg_from_subnet.assert_called_once_with(network_client=network_client,
                                                                             cloud_provider_model=cloud_provider_model,
                                                                             resource_group_name=tested_group_name,
                                                                             logger=self.logger)

        self.delete_operation.delete_sandbox_subnet.assert_called_once_with(network_client=network_client,
                                                                            cloud_provider_model=cloud_provider_model,
                                                                            resource_group_name=tested_group_name,
                                                                            logger=self.logger)

        self.delete_operation.delete_resource_group.assert_called_once_with(resource_client=resource_client,
                                                                            group_name=tested_group_name,
                                                                            logger=self.logger)

        self.delete_operation.delete_resource_group.assert_called_with(resource_client=resource_client,
                                                                       logger=self.logger,
                                                                       group_name=tested_group_name)

    def test_delete_sandbox_subnet_on_error(self):
        # Arrange
        self.vm_service.delete_resource_group = Mock()
        self.vm_service.delete_sandbox_subnet = Mock()
        tested_group_name = "test_group"
        vnet = Mock()
        subnet = Mock()
        subnet.name = "test_group_for_exception"
        vnet.subnets = [subnet]
        reservation = Mock()
        reservation.reservation_id = tested_group_name
        self.network_service.get_sandbox_virtual_network = Mock(return_value=vnet)

        # Act
        self.assertRaises(Exception,
                          self.delete_operation.delete_sandbox_subnet)

    def test_delete_operation(self):
        """
        :return:
        """

        # Arrange
        self.vm_service.delete_vm = Mock()
        network_client = Mock()
        storage_client = Mock()
        network_client.network_interfaces.delete = Mock()
        network_client.public_ip_addresses.delete = Mock()
        self.delete_operation.security_group_service.delete_security_rules = Mock()

        # Act
        self.delete_operation.delete(compute_client=Mock(),
                                     network_client=network_client,
                                     storage_client=storage_client,
                                     group_name="AzureTestGroup",
                                     vm_name="AzureTestVM",
                                     logger=self.logger)

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.delete_vm))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(network_client.public_ip_addresses.delete))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(network_client.network_interfaces.delete))
        self.delete_operation.generic_lock_provider.get_resource_lock.assert_called_with(lock_key="AzureTestGroup",
                                                                                         logger=self.logger)

    def test_delete_operation_on_error(self):
        # Arrange
        self.vm_service.delete_vm = Mock(side_effect=Exception("Boom!"))

        # Act
        self.assertRaises(Exception,
                          self.delete_operation.delete,
                          Mock(),
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
