from mock import Mock

from cloudshell.cp.azure.common.azure_clients import AzureClientsManager
from cloudshell.cp.azure.domain.services.command_cancellation import CommandCancellationService
from cloudshell.cp.azure.domain.services.task_waiter import TaskWaiterService
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from azure.mgmt.compute.models import Disk, CreationData, DiskCreateOption, Snapshot, HardwareProfile, NetworkProfile, \
    NetworkInterfaceReference, OSProfile, StorageProfile, OSDisk, DiskCreateOptionTypes, ManagedDiskParameters, \
    OperatingSystemTypes
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService

# from azure.mgmt.compute.v2018_06_01.models import Disk, CreationData, DiskCreateOption
# from azure.mgmt.compute.v2016_04_30_preview.models import Snapshot

cloud_provider = AzureCloudProviderResourceModel()
cloud_provider.azure_subscription_id = '4e556c5a-6bc6-4724-ac8a-ac2c14906549'
cloud_provider.azure_tenant = 'c55d955e-1ea6-4462-987a-ad33142ddffe'
cloud_provider.azure_application_id = 'f56e8ffd-c68d-4a49-8fc6-77b5dff8abe3'
cloud_provider.azure_application_key = 'Rotq2vvvQjW1zlnu6/gzuJbda8pEtjcO5d9/ObXKppQ='

clients = AzureClientsManager(cloud_provider)

snapshot = clients.compute_client.snapshots.get(resource_group_name='test',
                                                snapshot_name='test')

region = 'West Europe'
group_name = 'test'
# async_creation = clients.compute_client.disks.create_or_update(resource_group_name=group_name,
#                                                                disk_name='test-sds3d3d3345',
#                                                                disk=Disk(location=region,
#                                                                          creation_data=CreationData(
#                                                                              create_option=DiskCreateOption.copy,
#                                                                              source_resource_id=snapshot.id)))
# disk = async_creation.result()
disk = clients.compute_client.disks.get(resource_group_name=group_name, disk_name='test-sds3d3d3345')

vm_service = VirtualMachineService(TaskWaiterService(CommandCancellationService()))

nic = clients.network_client.network_interfaces.get(resource_group_name=group_name, network_interface_name='test-nic')

vm = vm_service._create_vm(compute_management_client=clients.compute_client,
                           region=region,
                           group_name=group_name,
                           vm_name='test-vj498g',
                           hardware_profile=HardwareProfile(vm_size='Standard_B2s'),
                           network_profile=NetworkProfile(network_interfaces=[NetworkInterfaceReference(id=nic.id)]),
                           # NOTE: OS Profile is not allowed in such VM type creation!!
                           os_profile=None,
                           storage_profile=StorageProfile(os_disk=OSDisk(create_option=DiskCreateOptionTypes.attach,
                                                                         os_type=OperatingSystemTypes.linux,
                                                                         managed_disk=ManagedDiskParameters(id=disk.id))),
                           cancellation_context=Mock(is_cancelled=False),
                           tags=None)

print("1")
