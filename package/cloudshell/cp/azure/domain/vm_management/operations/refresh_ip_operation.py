from msrestazure.azure_exceptions import CloudError


class RefreshIPOperation(object):
    def __init__(self, logger):
        """
        :param logger:
        :return:
        """
        self.logger = logger

    def refresh_ip(self, cloudshell_session, compute_client, network_client, resource_group_name, vm_name,
                   private_ip_on_resource, public_ip_on_resource, resource_fullname):
        """Refresh Public and Private IP on CloudShell resource from corresponding deployed Azure instance

        :param cloudshell_session: cloudshell.api.cloudshell_api.CloudShellAPISession instance
        :param compute_client: azure.mgmt.compute.ComputeManagementClient instance
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param resource_group_name: The name of the resource group
        :param vm_name: The name of the virtual machine
        :param private_ip_on_resource: private IP on the CloudShell resource
        :param public_ip_on_resource: public IP on the CloudShell resource
        :param resource_fullname: full resource name on the CloudShell
        :return
        """
        # NOTE: NIC and IP Address names must be same as a VM name
        nic = network_client.network_interfaces.get(resource_group_name, vm_name)
        private_ip_on_azure = nic.ip_configurations[0].private_ip_address
        try:
            pub_ip_addr = network_client.public_ip_addresses.get(resource_group_name, vm_name)
            public_ip_on_azure = pub_ip_addr.ip_address
        except CloudError:
            public_ip_on_azure = ""

        if public_ip_on_azure != public_ip_on_resource:
            cloudshell_session.SetAttributeValue(resource_fullname, "Public IP", public_ip_on_azure)

        if private_ip_on_azure != private_ip_on_resource:
            cloudshell_session.UpdateResourceAddress(resource_fullname, private_ip_on_azure)
