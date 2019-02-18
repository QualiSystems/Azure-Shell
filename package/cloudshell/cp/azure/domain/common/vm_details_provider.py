from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import StorageAccountTypes, VirtualMachine, Disk, CreationData
from azure.mgmt.network import NetworkManagementClient
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

    def create(self, instance, is_market_place, logger, group_name, network_client, compute_client):
        """
        :param group_name:
        :param NetworkManagementClient network_client:
        :param ComputeManagementClient compute_client:
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
            logger.info("VM {} was created via marketplace.".format(instance.name))
        else:
            vm_instance_data = self._get_vm_instance_data_for_vm_from_non_marketplace_image(instance,
                                                                                            compute_client,
                                                                                            group_name)
            vm_network_data = self._get_vm_network_data(instance, network_client, group_name, logger)
            logger.info("VM {} was created via NON marketplace.".format(instance.name))

        return VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data)

    @staticmethod
    def _get_vm_instance_data_for_market_place(instance):
        data = [
            VmDetailsProperty(key='Image Publisher', value=instance.storage_profile.image_reference.publisher),
            VmDetailsProperty(key='Image Offer', value=instance.storage_profile.image_reference.offer),
            VmDetailsProperty(key='Image SKU', value=instance.storage_profile.image_reference.sku),
            VmDetailsProperty(key='VM Size', value=instance.hardware_profile.vm_size),
            VmDetailsProperty(key='Operating System', value=instance.storage_profile.os_disk.os_type.name),
            VmDetailsProperty(key='Disk Type', value=
            'HDD' if instance.storage_profile.os_disk.managed_disk.storage_account_type == StorageAccountTypes.standard_lrs else 'SSD')
        ]
        return data

    def _get_vm_instance_data_for_vm_from_non_marketplace_image(self, instance, compute_client, group_name):
        """
        :param VirtualMachine instance:
        :param ComputeManagementClient compute_client:
        :param str group_name:
        :return:
        """
        data = []
        if instance.storage_profile.image_reference:
            # VM was created from a custom image
            image_name = self.resource_id_parser.get_image_name(resource_id=instance.storage_profile.image_reference.id)
            resource_group = self.resource_id_parser.get_resource_group_name(
                resource_id=instance.storage_profile.image_reference.id)

            data.append(VmDetailsProperty(key='Image', value=image_name))
            data.append(VmDetailsProperty(key='Image Resource Group', value=resource_group))
        else:
            # VM was created from a snapshot
            os_disk = compute_client.disks.get(resource_group_name=group_name,
                                               disk_name=instance.storage_profile.os_disk.name)  # type: Disk
            source_snapshot_id = os_disk.creation_data.source_uri
            source_snapshot_rg = self.resource_id_parser.get_resource_group_name(source_snapshot_id)
            source_snapshot_name = self.resource_id_parser.get_name_from_resource_id(source_snapshot_id)

            data.append(VmDetailsProperty(key='Snapshot', value=source_snapshot_name))
            data.append(VmDetailsProperty(key='Snapshot Resource Group', value=source_snapshot_rg))

        data.append(VmDetailsProperty(key='VM Size', value=instance.hardware_profile.vm_size))
        data.append(VmDetailsProperty(key='Operating System', value=instance.storage_profile.os_disk.os_type.name),)
        data.append(VmDetailsProperty(key='Disk Type', value=
            'HDD' if instance.storage_profile.os_disk.managed_disk.storage_account_type == StorageAccountTypes.standard_lrs else 'SSD'))

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
