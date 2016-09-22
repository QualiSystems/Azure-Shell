from unittest import TestCase

from mock import Mock

from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService


class TestServices(TestCase):
    def SetUp(self):
        pass

    def test_vm_service_create_vm(self):
        # Arrange
        vm_service = VirtualMachineService()
        compute_management_client = Mock()
        compute_management_client.virtual_machines = Mock()
        compute_management_client.virtual_machines.create_or_update = Mock(return_value=Mock())

        # Act
        vm_service.create_vm(compute_management_client=compute_management_client,
                             image_offer=Mock(),
                             image_publisher=Mock(),
                             image_sku=Mock(),
                             image_version=Mock(),
                             admin_password=Mock(),
                             admin_username=Mock(),
                             computer_name=Mock(),
                             group_name=Mock(),
                             nic_id=Mock(),
                             region=Mock(),
                             storage_name=Mock(),
                             vm_name=Mock(),
                             tags=Mock())

        # verify
        self.assertTrue(compute_management_client.virtual_machines.create_or_update.called)
