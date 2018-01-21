from unittest import TestCase

from azure.mgmt.compute.models import StorageAccountTypes
from mock import Mock, MagicMock

from cloudshell.cp.azure.domain.common.vm_details_provider import VmDetailsProvider


class TestVmDetailsProvider(TestCase):
    def setUp(self):
        self.resource_id_parser = MagicMock()
        self.network_service = MagicMock()
        self.vm_details_provider = VmDetailsProvider(self.network_service, self.resource_id_parser)
        self.logger = MagicMock()
        self.network_client = MagicMock()

    def test_prepare_vm_details_from_market(self):
        instance = Mock()
        instance.storage_profile.image_reference.publisher = 'Param 1'
        instance.storage_profile.image_reference.offer = 'Param 2'
        instance.storage_profile.image_reference.sku = 'Param 3'
        instance.hardware_profile.vm_size = 'Param 4'
        instance.storage_profile.os_disk.os_type.name = 'Param 5'
        instance.storage_profile.os_disk.managed_disk.storage_account_type = StorageAccountTypes.premium_lrs

        instance.network_interfaces = []

        vm_instance_data = self.vm_details_provider.create(instance, True, self.logger, self.network_client,
                                                           '').vm_instance_data

        self.assertTrue(
            self._get_value(vm_instance_data, 'Image Publisher') == instance.storage_profile.image_reference.publisher)
        self.assertTrue(
            self._get_value(vm_instance_data, 'Image Offer') == instance.storage_profile.image_reference.offer)
        self.assertTrue(self._get_value(vm_instance_data, 'Image SKU') == instance.storage_profile.image_reference.sku)
        self.assertTrue(self._get_value(vm_instance_data, 'VM Size') == instance.hardware_profile.vm_size)
        self.assertTrue(
            self._get_value(vm_instance_data, 'Operating System') == instance.storage_profile.os_disk.os_type.name)
        self.assertTrue(self._get_value(vm_instance_data, 'Disk Type') == 'SSD')

    def test_prepare_vm_details_from_image(self):
        instance = Mock()
        instance.network_interfaces = []
        resource_group = 'Group 1'
        self.resource_id_parser.get_image_name = Mock(return_value='Image Name')
        self.resource_id_parser.get_resource_group_name = Mock(return_value=resource_group)
        instance.hardware_profile.vm_size = 'Param 4'
        instance.storage_profile.os_disk.os_type.name = 'Param 5'
        instance.storage_profile.os_disk.managed_disk.storage_account_type = StorageAccountTypes.premium_lrs

        vm_instance_data = self.vm_details_provider.create(instance, False, self.logger, self.network_client,
                                                           resource_group).vm_instance_data

        self.assertTrue(self._get_value(vm_instance_data, 'Image') == 'Image Name')
        self.assertTrue(self._get_value(vm_instance_data, 'Image Resource Group') == resource_group)
        self.assertTrue(self._get_value(vm_instance_data, 'VM Size') == instance.hardware_profile.vm_size)
        self.assertTrue(
            self._get_value(vm_instance_data, 'Operating System') == instance.storage_profile.os_disk.os_type.name)
        self.assertTrue(self._get_value(vm_instance_data, 'Disk Type') == 'SSD')

    def test_prepare_vm_network_data(self):
        network_interface = Mock()
        network_interface.resource_guid = 'Param Guid'
        network_interface.name = 'Param Name'
        network_interface.primary = True
        network_interface.mac_address = 'Mac Param'
        ip_configuration = Mock()
        ip_configuration.private_ip_address = 'Param Ip Address'
        ip_configuration.public_ip_address = Mock()
        network_interface.ip_configurations = [ip_configuration]
        resource_group = 'Group 1'

        self.network_client.network_interfaces.get = Mock(return_value=network_interface)

        instance = Mock()
        instance.network_interfaces = [
            network_interface
        ]

        public_ip = Mock()
        public_ip.ip_address = 'Public Address Param'
        public_ip.public_ip_allocation_method = 'Public Method Param'
        self.network_service.get_public_ip = Mock(return_value=public_ip)

        network_interface_objects = self.vm_details_provider._get_vm_network_data(instance, self.network_client,
                                                                                  resource_group, self.logger)

        nic = network_interface_objects[0]

        self.assertTrue(nic['interface_id'] == network_interface.resource_guid)
        self.assertTrue(nic['network_id'] == network_interface.name)

        network_data = nic['network_data']

        ip = filter(lambda x: x['key'] == "IP", network_data)[0]
        self.assertTrue(ip['value'] == ip_configuration.private_ip_address)

        mac = filter(lambda x: x['key'] == "MAC Address", network_data)[0]
        self.assertTrue(mac['value'] == network_interface.mac_address)

        public_address = filter(lambda x: x['key'] == "Public IP", network_data)[0]
        self.assertTrue(public_address['value'] == public_ip.ip_address)

        public_method = filter(lambda x: x['key'] == "Public IP Type", network_data)[0]
        self.assertTrue(public_method['value'] == public_ip.public_ip_allocation_method)

    def _get_value(self, data, key):
        for item in data:
            if item['key'] == key:
                return item['value']
        return None
