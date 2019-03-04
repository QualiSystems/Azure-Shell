from azure.mgmt.compute.models import Snapshot, StorageAccountTypes, CreationData, DiskCreateOption
from cloudshell.cp.azure.common.azure_clients import AzureClientsManager
from cloudshell.cp.azure.common.parsers.azure_model_parser import AzureCloudProviderResourceModel
from cloudshell.cp.azure.common.parsers.azure_resource_id_parser import AzureResourceIdParser
from cloudshell.cp.azure.domain.services.task_waiter import TaskWaiterService
from cloudshell.cp.azure.domain.services.tags import TagService, TagNames
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.models.reservation_model import ReservationModel


class SnapshotOperation:
    TAG_SOURCE_VM_NAME = "SourceVmName"
    TAG_SNAPSHOT_PREFIX = "SnapshotPrefix"

    def __init__(self, vm_service, task_service, tags_service):
        """
        :param VirtualMachineService vm_service:
        :param TaskWaiterService task_service:
        :param TagService tags_service:
        """
        self.task_service = task_service
        self.vm_service = vm_service
        self.tags_service = tags_service

    def list(self, azure_clients, reservation, instance_name, snapshots_resource_group, logger):
        """
        Return a string that contains a comma separated list of snpashot names and their respective resource groups for
        current instance and current sandbox. If snapshots_resource_group is not provided will look for relevant
        snapshots in the entire subscription
        :param AzureClientsManager azure_clients:
        :param ReservationModel reservation:
        :param str instance_name:
        :param str snapshots_resource_group:
        :param logging.Logger logger:
        :rtype: str
        """
        if not snapshots_resource_group:
            snapshots = list(azure_clients.compute_client.snapshots.list())
        else:
            snapshots = list(azure_clients.compute_client.snapshots.list_by_resource_group(snapshots_resource_group))

        instance_name = instance_name.lower()

        my_snapshots = \
            list(filter(lambda x: x.tags and self.TAG_SOURCE_VM_NAME in x.tags
                                  and x.tags[self.TAG_SOURCE_VM_NAME].lower() == instance_name
                                  and TagNames.SandboxId in x.tags
                                  and x.tags[TagNames.SandboxId] == reservation.reservation_id, snapshots))

        results = []
        for snapshot in my_snapshots:
            results.append('{}/{}'.format(AzureResourceIdParser.get_resource_group_name(snapshot.id).lower(),
                                          snapshot.name))

        return ', '.join(results)

    def save(self, azure_clients, reservation, cloud_provider_model, instance_name, destination_resource_group,
             source_resource_group, snapshot_name_prefix, cancellation_context, logger, disk_type):
        """
        :type reservation: ReservationModel
        :type disk_type: str
        :type logger: logging.Logger
        :type cancellation_context:
        :type snapshot_name_prefix: str
        :type source_resource_group: str
        :type destination_resource_group: str
        :type instance_name: str
        :type cloud_provider_model: AzureCloudProviderResourceModel
        :type azure_clients: AzureClientsManager
        :rtype:  Snapshot
        """
        disk_type = self._get_and_validate_disk_type(disk_type)

        vm = self.vm_service.get_vm(azure_clients.compute_client, source_resource_group, instance_name)
        disk_name = vm.storage_profile.os_disk.name

        managed_disk = azure_clients.compute_client.disks.get(source_resource_group, disk_name)

        tags = self._prepare_snapshot_tags(instance_name, reservation, snapshot_name_prefix)

        snapshot_poller = azure_clients.compute_client.snapshots.create_or_update(
            destination_resource_group,
            "{0}{1}".format(snapshot_name_prefix, instance_name),
            Snapshot(location=cloud_provider_model.region,
                     account_type=disk_type,
                     tags=tags,
                     creation_data=CreationData(create_option=DiskCreateOption.copy,
                                                source_uri=managed_disk.id))
        )

        self.task_service.wait_for_task(operation_poller=snapshot_poller,
                                        cancellation_context=cancellation_context,
                                        logger=logger)

        snapshot = snapshot_poller.result()

        return snapshot

    def _prepare_snapshot_tags(self, instance_name, reservation, snapshot_name_prefix):
        tags = self.tags_service.get_tags(reservation=reservation)
        tags.update({self.TAG_SOURCE_VM_NAME: instance_name})
        if snapshot_name_prefix:
            tags.update({self.TAG_SNAPSHOT_PREFIX: snapshot_name_prefix})
        return tags

    def _get_and_validate_disk_type(self, disk_type):
        disk_type = disk_type.lower()

        if disk_type == "ssd":
            disk_type = StorageAccountTypes.premium_lrs

        elif disk_type == "hdd":
            disk_type = StorageAccountTypes.standard_lrs

        else:
            raise ValueError("disk type should be HDD/SDD")

        return disk_type
