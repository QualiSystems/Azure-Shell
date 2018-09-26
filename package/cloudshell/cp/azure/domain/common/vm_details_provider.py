from azure.mgmt.compute.models import StorageAccountTypes
from cloudshell.cp.core.models import VmDetailsProperty, VmDetailsData, VmDetailsNetworkInterface

from cloudshell.cp.azure.domain.vm_management.operations.deploy_operation import get_ip_from_interface_name


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
        vm_instance_data = None
        vm_network_data = None

        if is_market_place:
            vm_instance_data = self._get_vm_instance_data_for_market_place(instance)
            vm_network_data = self._get_vm_network_data(instance, network_client, group_name, logger)
            logger.info("VM {} was created via market place.".format(instance.name))
        else:
            vm_instance_data = self._get_vm_instance_data_for_custom_image(instance)
            vm_network_data = self._get_vm_network_data(instance, network_client, group_name, logger)
            logger.info("VM {} was created via custom image.".format(instance.name))

        return VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data)

    @staticmethod
    def _get_vm_instance_data_for_market_place(instance):
        data = [
            VmDetailsProperty(key='Image Publisher',value= instance.storage_profile.image_reference.publisher),
            VmDetailsProperty(key='Image Offer',value= instance.storage_profile.image_reference.offer),
            VmDetailsProperty(key='Image SKU',value= instance.storage_profile.image_reference.sku),
            VmDetailsProperty(key='VM Size',value= instance.hardware_profile.vm_size),
            VmDetailsProperty(key='Operating System',value= instance.storage_profile.os_disk.os_type.name),
            VmDetailsProperty(key='Disk Type',value=
                           'HDD' if instance.storage_profile.os_disk.managed_disk.storage_account_type == StorageAccountTypes.standard_lrs else 'SSD')
        ]
        return data

    def _get_vm_instance_data_for_custom_image(self, instance):
        image_name = self.resource_id_parser.get_image_name(resource_id=instance.storage_profile.image_reference.id)
        resource_group = self.resource_id_parser.get_resource_group_name(resource_id=instance.storage_profile.image_reference.id)

        data = [
            VmDetailsProperty(key='Image',value= image_name),
            VmDetailsProperty(key='Image Resource Group',value= resource_group),
            VmDetailsProperty(key='VM Size',value= instance.hardware_profile.vm_size),
            VmDetailsProperty(key='Operating System',value= instance.storage_profile.os_disk.os_type.name),
            VmDetailsProperty(key='Disk Type',value=
                           'HDD' if instance.storage_profile.os_disk.managed_disk.storage_account_type == StorageAccountTypes.standard_lrs else 'SSD')
        ]
        return data

    def _get_vm_network_data(self, instance, network_client, group_name, logger):

        network_interface_objects = []
        for network_interface in instance.network_profile.network_interfaces:
            nic_name = self.resource_id_parser.get_name_from_resource_id(network_interface.id)

            nic = network_client.network_interfaces.get(group_name, nic_name)

            ip_configuration = nic.ip_configurations[0]

            private_ip = ip_configuration.private_ip_address
            public_ip = ''
            network_data = [VmDetailsProperty(key="IP", value=ip_configuration.private_ip_address)]

            subnet_name = ip_configuration.subnet.id.split('/')[-1]

            current_interface = VmDetailsNetworkInterface(interfaceId=nic.resource_guid,
                                                          networkId=subnet_name,
                                                          isPrimary=nic.primary,
                                                          networkData=network_data,
                                                          privateIpAddress=private_ip,
                                                          publicIpAddress=public_ip)

            if ip_configuration.public_ip_address:
                public_ip_name = get_ip_from_interface_name(nic_name)

                public_ip_object = self.network_service.get_public_ip(network_client=network_client,
                                                                      group_name=group_name,
                                                                      ip_name=public_ip_name)
                public_ip = public_ip_object.ip_address

                network_data.append(VmDetailsProperty(key="Public IP", value=public_ip))
                network_data.append(
                    VmDetailsProperty(key="Public IP Type", value=public_ip_object.public_ip_allocation_method))
                # logger.info("VM {} was created with public IP '{}'.".format(instance.name,
                #                                                             ip_configuration.public_ip_address.ip_address))
                logger.info("VM {} was created with public IP '{}'.".format(instance.name, public_ip))

            network_data.append(VmDetailsProperty(key="MAC Address", value=nic.mac_address))

            network_interface_objects.append(current_interface)

        return network_interface_objects