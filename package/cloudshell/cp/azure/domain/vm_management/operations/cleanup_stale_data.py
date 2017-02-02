class CleanUpStaleDataOperation(object):

    def __init__(self, network_service, vm_service, resource_id_parser):
        """

        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.parsers.azure_model_parser.AzureModelsParser resource_id_parser:
        :return:
        """
        self.network_service = network_service
        self.vm_service = vm_service
        self.resource_id_parser = resource_id_parser

    def _get_connected_resource_groups(self, subnet):
        """Get all resource group names for connected to subnet resources

        :param azure.mgmt.network.models.subnet.Subnet subnet:
        :return: set of resource group names, connected to given subnet
        :rtype set
        """
        resource_groups = set()

        if subnet.network_security_group is not None:
            resource_group = self.resource_id_parser.get_resource_group_name(
                resource_id=subnet.network_security_group.id)
            resource_groups.add(resource_group)

        if subnet.ip_configurations:
            for ip_conf in subnet.ip_configurations:
                resource_group = self.resource_id_parser.get_resource_group_name(
                    resource_id=ip_conf.id)
                resource_groups.add(resource_group)

        return resource_groups

    def _get_active_resource_group(self, cloudshell_session):
        """Get list of the Resource Group names for the active Reservations

        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session:
        :return: list of Resource Group names
        :rtype: list[str]
        """
        active_reservations = cloudshell_session.GetCurrentReservations()
        return [reservation.Id for reservation in active_reservations.Reservations]

    def cleanup_stale_data(self, network_client, resource_client, cloud_provider_model, cloudshell_session, logger):
        """Clean up stale resources on Azure

        :param azure.mgmt.network.NetworkManagementClient network_client:
        :param azure.mgmt.resource.ResourceManagementClient resource_client:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session:
        :param logging.Logger logger:
        :return:
        """
        active_resource_groups = self._get_active_resource_group(cloudshell_session=cloudshell_session)
        logger.info("Resource groups for active reservations: {}".format(active_resource_groups))

        sandbox_vnetwork = self.network_service.get_sandbox_virtual_network(
            network_client=network_client,
            group_name=cloud_provider_model.management_group_name)

        for subnet in sandbox_vnetwork.subnets:
            logger.info("Checking subnet {}".format(subnet.id))

            if subnet.address_prefix in cloud_provider_model.networks_in_use:
                logger.info("Subnet {} is in 'Networks In Use' attribute, ignore it".format(subnet.id))
                continue

            resource_groups = self._get_connected_resource_groups(subnet=subnet)

            if not any(resource_group in active_resource_groups for resource_group in resource_groups):
                logger.info("Subnet {} is not related to any active reservation".format(subnet.id))

                if subnet.network_security_group is not None:
                    logger.info("Detaching NSG from subnet {}".format(subnet.id))

                    subnet.network_security_group = None
                    self.network_service.update_subnet(network_client=network_client,
                                                       resource_group_name=cloud_provider_model.management_group_name,
                                                       virtual_network_name=sandbox_vnetwork.name,
                                                       subnet_name=subnet.name,
                                                       subnet=subnet)
                    logger.info("NSG from subnet {} was successfully detached".format(subnet.id))

                for resource_group in resource_groups:
                    logger.info("Resource group {} of the connected to subnet resource is not in the active state. "
                                "Deleting resource group ".format(resource_group))

                    self.vm_service.delete_resource_group(resource_management_client=resource_client,
                                                          group_name=resource_group)

                    logger.info("Resource group {} was successfully deleted".format(resource_group))

                logger.info("Deleting Subnet {}...".format(subnet.id))
                self.network_service.delete_subnet(network_client=network_client,
                                                   group_name=cloud_provider_model.management_group_name,
                                                   vnet_name=sandbox_vnetwork.name,
                                                   subnet_name=subnet.name)

                logger.info("Subnet {} was successfully deleted".format(subnet.id))
