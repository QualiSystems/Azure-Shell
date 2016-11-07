from unittest import TestCase

from mock import Mock

from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.delete_operation import DeleteAzureVMOperation
from tests.helpers.test_helper import TestHelper


class TestCleanupConnectivity(TestCase):
    def setUp(self):
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.tags_service = TagService()
        self.delete_operation = DeleteAzureVMOperation(vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       tags_service=self.tags_service)

    def test_cleanup(self):
        """
        :return:
        """

        # Arrange
        self.vm_service.delete_resource_group = Mock()
        self.vm_service.delete_sandbox_subnet = Mock()
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
        self.delete_operation.delete_resource_group(resource_client=resource_client, group_name=tested_group_name)
        self.delete_operation.delete_sandbox_subnet(network_client=network_client,
                                                    cloud_provider_model=cloud_provider_model,
                                                    resource_group_name=tested_group_name)

        # Verify
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.delete_resource_group))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.network_service.get_sandbox_virtual_network))
        self.vm_service.delete_resource_group.assert_called_with(resource_management_client=resource_client,
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

