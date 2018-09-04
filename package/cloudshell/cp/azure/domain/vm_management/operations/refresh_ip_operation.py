class RefreshIPOperation(object):
    def __init__(self, vm_service, resource_id_parser):
        """

        :param vm_service: cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService
        :param resource_id_parser: cloudshell.cp.azure.common.parsers.azure_model_parser.AzureModelsParser
        :return:
        """
        self.vm_service = vm_service
        self.resource_id_parser = resource_id_parser

    def refresh_ip(self, cloudshell_session, compute_client, network_client, resource_group_name, vm_name,
                   private_ip_on_resource, public_ip_on_resource, resource_fullname, logger):
        """Refresh Public and Private IP on CloudShell resource from corresponding deployed Azure instance

        :param cloudshell_session: cloudshell.api.cloudshell_api.CloudShellAPISession instance
        :param compute_client: azure.mgmt.compute.ComputeManagementClient instance
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param resource_group_name: The name of the resource group
        :param vm_name: The name of the virtual machine
        :param private_ip_on_resource: private IP on the CloudShell resource
        :param public_ip_on_resource: public IP on the CloudShell resource
        :param resource_fullname: full resource name on the CloudShell
        :param logger: logging.Logger instance
        :return
        """
        # check if VM exists and in the correct state
        logger.info("Check that VM {} exists under resource group {} and is active".format(
                vm_name, resource_group_name))

        vm = self.vm_service.get_active_vm(
            compute_management_client=compute_client,
            group_name=resource_group_name,
            vm_name=vm_name)

        # find the primary nic
        primary_nic_ref = next(iter(filter(lambda x: x.primary, vm.network_profile.network_interfaces)), None)
        nic_reference = primary_nic_ref if primary_nic_ref else vm.network_profile.network_interfaces[0]
        nic_name = self.resource_id_parser.get_name_from_resource_id(nic_reference.id)
        logger.info("Retrieving NIC {} for VM {}".format(nic_name, vm_name))
        nic = network_client.network_interfaces.get(resource_group_name, nic_name)

        vm_ip_configuration = nic.ip_configurations[0]
        private_ip_on_azure = vm_ip_configuration.private_ip_address

        public_ip_reference = vm_ip_configuration.public_ip_address

        if public_ip_reference is None:
            logger.info("There is no Public IP attached to VM {}".format(vm_name))
            public_ip_on_azure = ""
        else:
            public_ip_name = self.resource_id_parser.get_name_from_resource_id(public_ip_reference.id)
            logger.info("Retrieving Public IP {} for VM {}".format(public_ip_name, vm_name))
            pub_ip_addr = network_client.public_ip_addresses.get(resource_group_name, public_ip_name)
            public_ip_on_azure = pub_ip_addr.ip_address

        logger.info("Public IP on Azure: '{}'".format(public_ip_on_azure))
        logger.info("Public IP on CloudShell: '{}'".format(public_ip_on_resource))

        if public_ip_on_azure != public_ip_on_resource:
            logger.info("Updating Public IP on the resource to '{}' ...".format(public_ip_on_azure))
            cloudshell_session.SetAttributeValue(resource_fullname, "Public IP", public_ip_on_azure)

        logger.info("Private IP on Azure: '{}'".format(private_ip_on_azure))
        logger.info("Private IP on CloudShell: '{}'".format(private_ip_on_resource))

        if private_ip_on_azure != private_ip_on_resource:
            logger.info("Updating Private IP on the resource to '{}' ...".format(private_ip_on_azure))
            cloudshell_session.UpdateResourceAddress(resource_fullname, private_ip_on_azure)
