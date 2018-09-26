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

        instance.network_profile = Mock()
        instance.network_profile.network_interfaces = MagicMock()

        vm_instance_data = self.vm_details_provider.create(instance, True, self.logger, self.network_client,
                                                           '').vmInstanceData

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
        instance.network_profile = Mock()
        instance.network_profile.network_interfaces = MagicMock()
        resource_group = 'Group 1'
        self.resource_id_parser.get_image_name = Mock(return_value='Image Name')
        self.resource_id_parser.get_resource_group_name = Mock(return_value=resource_group)
        instance.hardware_profile.vm_size = 'Param 4'
        instance.storage_profile.os_disk.os_type.name = 'Param 5'
        instance.storage_profile.os_disk.managed_disk.storage_account_type = StorageAccountTypes.premium_lrs

        vm_instance_data = self.vm_details_provider.create(instance, False, self.logger, self.network_client,
                                                           resource_group).vmInstanceData

        self.assertTrue(self._get_value(vm_instance_data, 'Image') == 'Image Name')
        self.assertTrue(self._get_value(vm_instance_data, 'Image Resource Group') == resource_group)
        self.assertTrue(self._get_value(vm_instance_data, 'VM Size') == instance.hardware_profile.vm_size)
        self.assertTrue(
            self._get_value(vm_instance_data, 'Operating System') == instance.storage_profile.os_disk.os_type.name)
        self.assertTrue(self._get_value(vm_instance_data, 'Disk Type') == 'SSD')

    def test_prepare_vm_network_data_single_nic(self):
        network_interface = Mock()
        network_interface.resource_guid = 'Param Guid'
        network_interface.name = 'Param Name'
        network_interface.primary = True
        network_interface.mac_address = 'Mac Param'
        ip_configuration = Mock()
        ip_configuration.private_ip_address = 'Param Ip Address'
        ip_configuration.public_ip_address = Mock()
        ip_configuration.subnet.id = 'a/a'
        network_interface.ip_configurations = [ip_configuration]
        resource_group = 'Group 1'

        self.network_client.network_interfaces.get = Mock(return_value=network_interface)

        nic = Mock()
        nic.id = "/azure_resource_id/nic_name"
        instance = Mock()
        instance.network_profile = Mock()
        instance.network_profile.network_interfaces = [nic]

        public_ip = Mock()
        public_ip.ip_address = 'Public Address Param'
        public_ip.public_ip_allocation_method = 'Public Method Param'
        self.network_service.get_public_ip = Mock(return_value=public_ip)

        network_interface_objects = self.vm_details_provider._get_vm_network_data(instance, self.network_client,
                                                                                  resource_group, self.logger)

        nic = network_interface_objects[0]

        self.assertTrue(nic.interfaceId == network_interface.resource_guid)
        self.assertTrue(nic.networkId == ip_configuration.subnet.id.split('/')[-1])

        network_data = nic.networkData

        self.assertTrue(self._get_value(network_data, 'IP') == ip_configuration.private_ip_address)
        self.assertTrue(self._get_value(network_data, 'MAC Address') == network_interface.mac_address)
        self.assertTrue(self._get_value(network_data, 'Public IP') == public_ip.ip_address)
        self.assertTrue(self._get_value(network_data, "Public IP Type") == public_ip.public_ip_allocation_method)

    def _get_value(self, data, key):
        for item in data:
            if item.key == key:
                return item.value
        return None
