from azure.mgmt.compute.models import Snapshot, StorageAccountTypes, CreationData, DiskCreateOption


class SnapshotOperation:
    def __init__(self, vm_service, task_service):
        """

        :param vm_service:
        :param task_service: cloudshell.cp.azure.domain.services.task_waiter.TaskWaiterService
        :return: azure.mgmt.compute.models.Snapshot
        """
        self.task_service = task_service
        self.vm_service = vm_service

    def save(self,
             azure_clients,
             cloud_provider_model,
             instance_name,
             destination_resource_group,
             source_resource_group,
             snapshot_name_prefix,
             cancellation_context,
             logger,
             disk_type='Standard_LRS'):
        """
        :return:  azure.mgmt.compute.models.Snapshot
        """

        vm = self.vm_service.get_vm(azure_clients.compute_client, source_resource_group, instance_name)
        disk_name = vm.storage_profile.os_disk.name

        managed_disk = azure_clients.compute_client.disks.get(source_resource_group, disk_name)

        snapshot_poller = azure_clients.compute_client.snapshots.create_or_update(
            destination_resource_group,
            "{0}{1}".format(snapshot_name_prefix, instance_name),
            Snapshot(location=cloud_provider_model.region,
                     account_type=disk_type,
                     creation_data=CreationData(create_option=DiskCreateOption.copy,
                                                source_uri=managed_disk.id))
        )

        self.task_service.wait_for_task(operation_poller=snapshot_poller,
                                        cancellation_context=cancellation_context,
                                        logger=logger)

        snapshot = snapshot_poller.result()

        return snapshot
