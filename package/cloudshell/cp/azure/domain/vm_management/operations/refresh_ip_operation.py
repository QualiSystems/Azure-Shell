from msrestazure.azure_exceptions import CloudError


class RefreshIPOperation(object):

    def __init__(self, vm_service):
        """
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :return:
        """
        self.vm_service = vm_service

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
        # NOTE: NIC and IP Address names must be same as a VM name
        # check if VM exists and in the correct state
        logger.info("Check that VM {} exists under resource group {} and is active".format(
            vm_name, resource_group_name))

        self.vm_service.get_active_vm(
            compute_management_client=compute_client,
            group_name=resource_group_name,
            vm_name=vm_name)

        try:
            nic = network_client.network_interfaces.get(resource_group_name, vm_name)
            private_ip_on_azure = nic.ip_configurations[0].private_ip_address
        except CloudError:
            logger.info("Cant find NIC {} under resource group {}".format(vm_name, resource_group_name),
                        exc_info=True)
            private_ip_on_azure = ""

        try:
            pub_ip_addr = network_client.public_ip_addresses.get(resource_group_name, vm_name)
            public_ip_on_azure = pub_ip_addr.ip_address
        except CloudError:
            logger.info("Cant find Public IP {} under resource group {}".format(vm_name, resource_group_name),
                        exc_info=True)
            public_ip_on_azure = ""

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
