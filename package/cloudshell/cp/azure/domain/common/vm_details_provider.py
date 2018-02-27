from azure.mgmt.compute.models import StorageAccountTypes


class VmDetailsProvider(object):
    def __init__(self, network_service, resource_id_parser):
        """
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param AzureResourceIdParser resource_id_parser:
        :return:
        """
        self.network_service = network_service
        self.resource_id_parser = resource_id_parser

    def create(self, instance, is_market_place, logger, network_client, group_name):
        """
        :param group_name:
        :param network_client:
        :param instance: azure.mgmt.compute.models.VirtualMachine
        :param is_market_place: bool
        :param logging.Logger logger:
        :return:
        """

        vm_details = VmDetails(instance.name)

        if is_market_place:
            vm_details.vm_instance_data = self._get_vm_instance_data_for_market_place(instance)
            vm_details.vm_network_data = self._get_vm_network_data(instance, network_client, group_name, logger)
            logger.info("VM {} was created via market place.".format(instance.name))
        else:
            vm_details.vm_instance_data = self._get_vm_instance_data_for_custom_image(instance)
            vm_details.vm_network_data = self._get_vm_network_data(instance, network_client, group_name, logger)
            logger.info("VM {} was created via custom image.".format(instance.name))

        return vm_details

    @staticmethod
    def _get_vm_instance_data_for_market_place(instance):
        data = [
            AdditionalData('Image Publisher', instance.storage_profile.image_reference.publisher),
            AdditionalData('Image Offer', instance.storage_profile.image_reference.offer),
            AdditionalData('Image SKU', instance.storage_profile.image_reference.sku),
            AdditionalData('VM Size', instance.hardware_profile.vm_size),
            AdditionalData('Operating System', instance.storage_profile.os_disk.os_type.name),
            AdditionalData('Disk Type',
                           'HDD' if instance.storage_profile.os_disk.managed_disk.storage_account_type == StorageAccountTypes.standard_lrs else 'SSD')
        ]
        return data

    def _get_vm_instance_data_for_custom_image(self, instance):
        image_name = self.resource_id_parser.get_image_name(resource_id=instance.storage_profile.image_reference.id)
        resource_group = self.resource_id_parser.get_resource_group_name(resource_id=instance.storage_profile.image_reference.id)

        data = [
            AdditionalData('Image', image_name),
            AdditionalData('Image Resource Group', resource_group),
            AdditionalData('VM Size', instance.hardware_profile.vm_size),
            AdditionalData('Operating System', instance.storage_profile.os_disk.os_type.name),
            AdditionalData('Disk Type',
                           'HDD' if instance.storage_profile.os_disk.managed_disk.storage_account_type == StorageAccountTypes.standard_lrs else 'SSD')
        ]
        return data

    def _get_vm_network_data(self, instance, network_client, group_name, logger):
        network_interface_objects = []

        nic = network_client.network_interfaces.get(group_name, instance.name)

        ip_configuration = nic.ip_configurations[0]

        network_interface_object = {
            "interface_id": nic.resource_guid,
            "network_id": nic.name,
            "network_data": [AdditionalData("IP", ip_configuration.private_ip_address)],
            "is_primary": nic.primary
        }

        if ip_configuration.public_ip_address:
            public_ip = self.network_service.get_public_ip(network_client=network_client,
                                                           group_name=group_name,
                                                           ip_name=instance.name)
            network_interface_object["network_data"].append(AdditionalData("Public IP", public_ip.ip_address))
            network_interface_object["network_data"].append(AdditionalData("Public IP Type", public_ip.public_ip_allocation_method))
            logger.info("VM {} was created with public IP '{}'.".format(instance.name,
                                                                        ip_configuration.public_ip_address.ip_address))

        network_interface_object["network_data"].append(AdditionalData("MAC Address", nic.mac_address))

        network_interface_objects.append(network_interface_object)

        return network_interface_objects


class VmDetails(object):
    def __init__(self, app_name):
        self.app_name = app_name
        self.error = None
        self.vm_instance_data = {}  # type: dict
        self.vm_network_data = []  # type: list[VmNetworkData]


class VmNetworkData(object):
    def __init__(self):
        self.interface_id = {}  # type: str
        self.network_id = {}  # type: str
        self.is_primary = False  # type: bool
        self.network_data = {}  # type: dict


def AdditionalData(key, value, hidden=False):
    """
    :type key: str
    :type value: str
    :type hidden: bool
    """
    return {
        "key": key,
        "value": value,
        "hidden": hidden
    }
