from unittest import TestCase

from mock import Mock, MagicMock

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.security_group import SecurityGroupService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.delete_operation import DeleteAzureVMOperation
from tests.helpers.test_helper import TestHelper


class TestCleanupConnectivity(TestCase):
    def setUp(self):
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.tags_service = TagService()
        self.security_group_service = SecurityGroupService()
        self.delete_operation = DeleteAzureVMOperation(vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       tags_service=self.tags_service,
                                                       security_group_service=self.security_group_service)
        self.logger = MagicMock()

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
        self.assertTrue(result['success'] == False)
        self.assertTrue(
            result['errorMessage'] == 'CleanupConnectivity ended with the error: {0}'.format(test_exception_message))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.logger.error))

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
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.delete_operation.remove_nsg_from_subnet))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.delete_operation.delete_sandbox_subnet))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.delete_operation.delete_resource_group))
        self.delete_operation.delete_resource_group.assert_called_with(resource_client=resource_client,
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
                          self.delete_operation.delete_sandbox_subnet,
                          )
