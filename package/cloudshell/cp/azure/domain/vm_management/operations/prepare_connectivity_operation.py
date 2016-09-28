from platform import machine


class PrepareConnectivityOperation(object):
    def __init__(self,
                 logger,
                 vm_service,
                 network_service,
                 storage_service,
                 tags_service):
        """

        :param logger:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :return:
        """

        self.logger = logger
        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.tags_service = tags_service

    def prepare_connectivity(self,
                             reservation,
                             cloud_provider_model,
                             storage_client,
                             resource_client,
                             network_client):
        """

        :param network_client:
        :param storage_client:
        :param resource_client:
        :param reservation: cloudshell.cp.azure.models.reservation_model.ReservationModel
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :return:
        """

        resource_name = "base name"
        admin_username = resource_name

        reservation_id = reservation.reservation_id
        group_name = str(reservation_id)
        admin_password = 'ScJaw12deDFG'
        storage_account_name = reservation_id

        # todo this should be reafctored the tags service should not return
        # all of these tags for the creation of a resource group
        tags = self.tags_service.get_tags("", admin_username, "", reservation)

        # 1. Crate a resource group
        self.vm_service.create_resource_group(resource_management_client=resource_client,
                                              group_name=group_name,
                                              region=cloud_provider_model.region,
                                              tags=tags)

        # 2. Create a storage account
        self.storage_service.create_storage_account(storage_client=storage_client,
                                                    group_name=group_name,
                                                    region=cloud_provider_model.region,
                                                    storage_account_name=storage_account_name,
                                                    tags=tags)

        # 3. Create the network interface
        self.network_service.create_virtual_network(management_group_name=group_name,
                                                    network_client=network_client,
                                                    network_name=resource_name,
                                                    region=cloud_provider_model.region,
                                                    subnet_name=resource_name,
                                                    tags=tags)

        raise Exception("the prepare connectivity is not working")
