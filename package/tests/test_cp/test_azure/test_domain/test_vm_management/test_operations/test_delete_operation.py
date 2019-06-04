from threading import Lock
from unittest import TestCase

from azure.mgmt.compute.models import NetworkInterfaceReference
from mock import Mock, MagicMock
from msrestazure.azure_exceptions import CloudError
from requests import Response

from cloudshell.cp.azure.domain.services.ip_service import IpService
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.domain.services.security_group import SecurityGroupService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.domain.vm_management.operations.delete_operation import DeleteAzureVMOperation


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
        self.ip_service = IpService(self.generic_lock_provider)
        self.delete_operation = DeleteAzureVMOperation(vm_service=self.vm_service,
                                                       network_service=self.network_service,
                                                       tags_service=self.tags_service,
                                                       security_group_service=self.security_group_service,
                                                       storage_service=self.storage_service,
                                                       generic_lock_provider=self.generic_lock_provider,
                                                       subnet_locker=Lock(),
                                                       ip_service=self.ip_service)

    def test_cleanup_on_error(self):
        # Arrange
        test_exception_message = "lalala"
        self.delete_operation.remove_nsg_and_routetable_from_subnets = Mock(side_effect=Exception(test_exception_message))
        self.delete_operation.delete_sandbox_subnets = Mock()

        # Act
        result = self.delete_operation.cleanup_connectivity(network_client=Mock(),
                                                            resource_client=Mock(),
                                                            cloud_provider_model=Mock(),
                                                            resource_group_name=Mock(),
                                                            request=Mock(actions=[Mock(type="cleanupNetwork")]),
                                                            logger=self.logger)

        # Verify
        self.assertFalse(result['success'])
        self.assertEqual(result['errorMessage'],
                         "CleanupSandboxInfra ended with the error(s): ['lalala']".format(test_exception_message))
        self.logger.exception.assert_called()

    def test_cleanup(self):
        """
        :return:
        """

        # Arrange
        self.delete_operation.remove_nsg_and_routetable_from_subnets = Mock()
        self.delete_operation.delete_resource_group = Mock()
        self.delete_operation.delete_sandbox_subnets = Mock()
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

        action = Mock(type="cleanupNetwork")
        request = Mock(actions=[action])

        # Act
        self.delete_operation.cleanup_connectivity(network_client=network_client,
                                                   resource_client=resource_client,
                                                   cloud_provider_model=cloud_provider_model,
                                                   resource_group_name=tested_group_name,
                                                   request=request,
                                                   logger=self.logger)

        # Verify
        self.delete_operation.remove_nsg_and_routetable_from_subnets.assert_called_once_with(network_client=network_client,
                                                                                             cloud_provider_model=cloud_provider_model,
                                                                                             resource_group_name=tested_group_name,
                                                                                             logger=self.logger)

        self.delete_operation.delete_sandbox_subnets.assert_called_once_with(network_client=network_client,
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
                          self.delete_operation.delete_sandbox_subnets)

    def test_delete_operation(self):
        """
        :return:
        """

        # Arrange
        vm = Mock()
        vm.network_profile.network_interfaces = [NetworkInterfaceReference(id='1/1/1/1')]
        self.vm_service.delete_vm = Mock()
        self.vm_service.get_vm = Mock(return_value=vm)
        network_client = self._prepare_mock_network_client()
        storage_client = Mock()
        compute_client = Mock()
        compute_client.virtual_machines.get.return_value = vm
        group_name = "AzureTestGroup"
        network_client.network_interfaces.delete = Mock()
        network_client.public_ip_addresses.delete = Mock()
        nsg = Mock()
        nsg.name = 'lol'
        network_client.network_security_groups.list = Mock(return_value=[nsg])
        self.delete_operation.security_group_service.delete_security_rules = Mock()
        self.delete_operation._delete_vm_disk = Mock()

        # Act
        self.delete_operation.delete(compute_client=compute_client,
                                     network_client=network_client,
                                     storage_client=storage_client,
                                     group_name=group_name,
                                     vm_name="AzureTestVM",
                                     logger=self.logger,
                                     cloudshell_session=MagicMock())

        # Verify
        self.vm_service.delete_vm.assert_called()
        network_client.public_ip_addresses.delete.assert_called()
        network_client.network_interfaces.delete.assert_called()
        self.delete_operation._delete_vm_disk.assert_called_once_with(
                logger=self.logger,
                storage_client=storage_client,
                compute_client=compute_client,
                group_name=group_name,
                vm=vm)

    def test_delete_operation_on_error(self):
        # Arrange
        self.vm_service.delete_vm = Mock(side_effect=Exception("Boom!"))
        compute_client = self._prepare_mock_compute_client()
        network_client = self._prepare_mock_network_client()
        nsg = Mock()
        nsg.name = 'lol'
        network_client.network_security_groups.list = Mock(return_value=[nsg])
        self.delete_operation.security_group_service.delete_security_rules = Mock()
        self.delete_operation._delete_vm_disk = Mock()

        # Act

        self.assertRaises(Exception,
                          self.delete_operation.delete,
                          compute_client,
                          network_client,
                          Mock(),
                          "AzureTestGroup",
                          "AzureTestVM",
                          self.logger,
                          Mock())

        # Verify
        self.logger.exception.assert_called()

    def _prepare_mock_compute_client(self):
        vm = Mock()
        vm.network_profile.network_interfaces = [NetworkInterfaceReference(id='1/1/1/1')]
        compute_client = Mock()
        compute_client.virtual_machines.get.return_value = vm
        return compute_client

    def _prepare_mock_network_client(self):
        network_client = Mock()
        network_interface = Mock()
        ip_configuration = Mock()
        ip_configuration.public_ip_address.id = '55.55.55.55'
        network_interface.ip_configurations = [ip_configuration]
        network_interface.network_security_group.id = 'eth0/interfaceName'
        network_client.network_interfaces.get.return_value = network_interface
        return network_client

    def test_delete_operation_on_cloud_error_not_found_no_exception(self):
        # Arrange
        response = Response()
        response.status_code = 0
        response.reason = 'Not Found'
        response.encoding = 'UTF-8'
        error = CloudError(response)
        self.vm_service.delete_vm = Mock(side_effect=error)
        self.delete_operation.security_group_service.delete_security_rules = Mock()
        compute_client = self._prepare_mock_compute_client()
        network_client = self._prepare_mock_network_client()
        nsg = Mock()
        nsg.name = 'lol'
        network_client.network_security_groups.list = Mock(return_value=[nsg])
        self.delete_operation._delete_vm_disk = Mock()

        # Act
        self.delete_operation.delete(
                compute_client,
                network_client,
                Mock(),
                "group_name",
                "vm_name",
                self.logger,
                cloudshell_session=MagicMock())

        # Verify
        self.logger.info.assert_called()

    def test_delete_operation_on_cloud_any_error_throws_exception(self):
        # Arrange
        response = Response()
        response.status_code = 0
        response.reason = "Bla bla error"
        response.encoding = 'UTF-8'
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

    def test_delete_vm_disk_vhd(self):
        # Arrange
        logger = Mock()
        storage_client = Mock()
        compute_client = Mock()
        group_name = Mock()
        vm = Mock()
        vm.storage_profile.os_disk.vhd = Mock()
        vm.storage_profile.os_disk.managed_disk = None

        self.delete_operation._delete_vhd_disk = Mock()
        self.delete_operation._delete_managed_disk = Mock()

        # Act
        self.delete_operation._delete_vm_disk(logger=logger,
                                              storage_client=storage_client,
                                              compute_client=compute_client,
                                              group_name=group_name,
                                              vm=vm)

        # Assert
        self.delete_operation._delete_managed_disk.assert_not_called()
        self.delete_operation._delete_vhd_disk.assert_called_once_with(
                storage_client=storage_client,
                group_name=group_name,
                logger=logger,
                vhd_url=vm.storage_profile.os_disk.vhd.uri)

    def test_delete_vm_disk_managed_disk(self):
        # Arrange
        logger = Mock()
        storage_client = Mock()
        compute_client = Mock()
        group_name = Mock()
        vm = Mock()
        vm.storage_profile.os_disk.vhd = None
        vm.storage_profile.os_disk.managed_disk = Mock()

        self.delete_operation._delete_vhd_disk = Mock()
        self.delete_operation._delete_managed_disk = Mock()

        # Act
        self.delete_operation._delete_vm_disk(logger=logger,
                                              storage_client=storage_client,
                                              compute_client=compute_client,
                                              group_name=group_name,
                                              vm=vm)

        # Assert
        self.delete_operation._delete_vhd_disk.assert_not_called()
        self.delete_operation._delete_managed_disk.assert_called_once_with(
                compute_client=compute_client,
                group_name=group_name,
                logger=logger,
                managed_disk_name=vm.storage_profile.os_disk.name)

    def test_delete_managed_disk(self):
        # Arrange
        logger = Mock()
        compute_client = Mock()
        group_name = Mock()
        managed_disk_name = Mock()
        self.vm_service.delete_managed_disk = Mock()

        # Act
        self.delete_operation._delete_managed_disk(logger=logger,
                                                   compute_client=compute_client,
                                                   group_name=group_name,
                                                   managed_disk_name=managed_disk_name)

        # Assert
        self.vm_service.delete_managed_disk.assert_called_once_with(compute_management_client=compute_client,
                                                                    resource_group=group_name,
                                                                    disk_name=managed_disk_name)

    def test_remove_nsg_and_routetable_from_subnets(self):
        resource_group_name = 'my_sandbox'
        network_client = Mock()
        cloud_provider_model = Mock()
        cloud_provider_model.management_group_name = resource_group_name
        logger = Mock()
        virtual_network = Mock()
        virtual_network.name = 'trololo'
        subnet = Mock()
        subnet.name = resource_group_name
        virtual_network.subnets = [subnet]
        self.network_service.get_sandbox_virtual_network = Mock()
        self.network_service.get_sandbox_virtual_network.return_value = virtual_network
        self.network_service.update_subnet = Mock()

        # Act
        self.delete_operation.remove_nsg_and_routetable_from_subnets(network_client,
                                                                     resource_group_name,
                                                                     cloud_provider_model,
                                                                     logger)

        # Verify
        self.network_service.update_subnet.assert_called_with(network_client=network_client,
                                                              resource_group_name=resource_group_name,
                                                              virtual_network_name=virtual_network.name,
                                                              subnet_name=subnet.name,
                                                              subnet=subnet)

    def test_delete_sandbox_subnets(self):
        resource_group_name = 'my_sandbox'
        network_client = Mock()
        cloud_provider_model = Mock()
        logger = Mock()
        cloud_provider_model.management_group_name = resource_group_name
        virtual_network = Mock()
        virtual_network.name = 'trololo'
        subnet = Mock()
        subnet.name = resource_group_name
        virtual_network.subnets = [subnet]
        self.network_service.get_sandbox_virtual_network = Mock()
        self.network_service.get_sandbox_virtual_network.return_value = virtual_network
        self.network_service.delete_subnet = Mock()

        self.delete_operation.delete_sandbox_subnets(network_client,
                                                     cloud_provider_model,
                                                     resource_group_name,
                                                     logger)

        self.network_service.delete_subnet.assert_called_with(network_client=network_client,
                                                              group_name=resource_group_name,
                                                              vnet_name=virtual_network.name,
                                                              subnet_name=subnet.name)
