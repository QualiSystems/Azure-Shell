import azure
from azure.mgmt.compute.models import OSProfile, HardwareProfile, VirtualMachineSizeTypes, NetworkProfile, \
    NetworkInterfaceReference, CachingTypes, DiskCreateOptionTypes, VirtualHardDisk, ImageReference, OSDisk, \
    VirtualMachine, StorageProfile
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.storage.models import SkuName


class VirtualMachineService(object):
    def __init__(self):
        pass

    def get_vm(self, compute_management_client, group_name, vm_name):
        """

        :param compute_management_client:
        :param group_name:
        :param vm_name:
        :return: azure.mgmt.compute.models.VirtualMachine
        """

        return compute_management_client.virtual_machines.get(group_name, vm_name)

    def create_vm(self,
                  compute_management_client,
                  image_offer,
                  image_publisher,
                  image_sku,
                  image_version,
                  admin_password,
                  admin_username,
                  computer_name,
                  group_name,
                  nic_id,
                  region,
                  storage_name,
                  vm_name,
                  tags):
        """

        :param compute_management_client:
        :param image_offer:
        :param image_publisher:
        :param image_sku:
        :param image_version:
        :param admin_password:
        :param admin_username:
        :param computer_name:
        :param group_name:
        :param nic_id:
        :param region:
        :param storage_name:
        :param vm_name:
        :param tags:
        :return:
        """
        os_profile = OSProfile(admin_username=admin_username, admin_password=admin_password,computer_name=computer_name)

        hardware_profile = HardwareProfile(vm_size=VirtualMachineSizeTypes.basic_a0)

        network_profile = NetworkProfile(network_interfaces=[NetworkInterfaceReference(id=nic_id)])

        vhd_format = 'https://{0}.blob.core.windows.net/vhds/{1}.vhd'.format(storage_name, vm_name)

        vhd = VirtualHardDisk(uri=vhd_format)

        os_disk = OSDisk(caching=CachingTypes.none,
                         create_option=DiskCreateOptionTypes.from_image,
                         name=storage_name,
                         vhd=vhd)

        image_reference = ImageReference(publisher=image_publisher, offer=image_offer, sku=image_sku,
                                         version=image_version)

        storage_profile = StorageProfile(os_disk=os_disk, image_reference=image_reference)

        virtual_machine = VirtualMachine(location=region,
                                         tags=tags,
                                         os_profile=os_profile,
                                         hardware_profile=hardware_profile,
                                         network_profile=network_profile,
                                         storage_profile=storage_profile)

        vm_result = compute_management_client.virtual_machines.create_or_update(group_name, vm_name, virtual_machine)

        return vm_result.result()

    def create_resource_group(self, resource_management_client, group_name, region):
        return resource_management_client.resource_groups.create_or_update(group_name,ResourceGroup(location=region))
