class SnapshotOperation:
    def __init__(self, vm_service):
        self.vm_service = vm_service

    def save(self,
             azure_clients,
             cloud_provider_model,
             instance_name,
             destination_resource_group,
             source_resource_group,
             snapshot_name_prefix):

        vm = self.vm_service.get_vm(azure_clients.compute_client, source_resource_group, instance_name)
        disk_name = vm.storage_profile.os_disk.name

        managed_disk = azure_clients.compute_client.disks.get(source_resource_group, disk_name)

        async_snapshot_creation = azure_clients.compute_client.snapshots.create_or_update(
            destination_resource_group,
            "{0}{1}".format(snapshot_name_prefix, instance_name),
            {
                'location': cloud_provider_model.region,
                'creation_data': {
                    'create_option': 'Copy',
                    'source_uri': managed_disk.id
                }
            }
        )

        snapshot = async_snapshot_creation.result()

        return snapshot

