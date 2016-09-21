import azure
from azure.mgmt.compute.models import OSProfile, HardwareProfile, VirtualMachineSizeTypes, NetworkProfile, \
    NetworkInterfaceReference, CachingTypes, DiskCreateOptionTypes, VirtualHardDisk, ImageReference, OSDisk
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.storage.models import SkuName


class VirtualMachineService(object):
    def __init__(self, compute_management_client, resource_management_client):
        self.compute_management_client = compute_management_client
        self.resource_management_client = resource_management_client

    def get_vm(self, group_name, vm_name):
        """

        :param group_name:
        :param vm_name:
        :return: azure.mgmt.compute.models.VirtualMachine
        """

        return self.compute_management_client.virtual_machines.get(group_name, vm_name)

    def create_vm(self, image_offer, image_publisher, image_sku, image_version, admin_password, admin_username,
                  computer_name, group_name, nic_id, region, storage_name, vm_name, tags):
        vm_result = self.compute_management_client.virtual_machines.create_or_update(
            group_name,
            vm_name,
            azure.mgmt.compute.models.VirtualMachine(
                location=region,
                tags=tags,
                os_profile=OSProfile(
                    admin_username=admin_username,
                    admin_password=admin_password,
                    computer_name=computer_name,
                ),
                hardware_profile=HardwareProfile(
                    vm_size=VirtualMachineSizeTypes.basic_a0
                ),
                network_profile=NetworkProfile(
                    network_interfaces=[
                        NetworkInterfaceReference(
                            id=nic_id
                        ),
                    ],
                ),
                storage_profile=azure.mgmt.compute.models.StorageProfile(
                    os_disk=OSDisk(
                        caching=CachingTypes.none,
                        create_option=DiskCreateOptionTypes.from_image,
                        name=storage_name,
                        vhd=VirtualHardDisk(
                            uri='https://{0}.blob.core.windows.net/vhds/{1}.vhd'.format(
                                storage_name,
                                vm_name,  # the VM name
                            ),
                        ),
                    ),
                    image_reference=ImageReference(
                        publisher=image_publisher,
                        offer=image_offer,
                        sku=image_sku,
                        version=image_version
                    ),
                ),
            ),
        )
        return vm_result.result()

    def create_resource_group(self, group_name, region):
        return self.resource_management_client.resource_groups.create_or_update(
            group_name,
            ResourceGroup(location=region)
        )


