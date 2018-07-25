class PowerAzureVMOperation(object):
    def __init__(self, vm_service, vm_custom_params_extractor):
        """
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.common.parsers.custom_param_extractor.VmCustomParamsExtractor vm_custom_params_extractor:
        :return:
        """
        self.vm_service = vm_service
        self.vm_custom_params_extractor = vm_custom_params_extractor

    def power_on(self, compute_client, resource_group_name, resource_full_name, data_holder, cloudshell_session):
        """Power on Azure VM instance

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param str resource_group_name: The name of the resource group.
        :param str resource_full_name: full resource name on the CloudShell
        :param cloudshell.cp.azure.common.deploy_data_holder.DeployDataHolder data_holder:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session:
        :return
        """
        vm_name = data_holder.name

        extension_time_out = self.vm_custom_params_extractor.get_custom_param_value(
            data_holder.vmdetails.vmCustomParams,
            "extension_time_out")

        # todo: move to some generic convert to boolean function
        if extension_time_out in ["True", "true", "1"]:
            cloudshell_session.SetResourceLiveStatus(resource_full_name, "Error", "Partially deployed app")

            raise Exception("Partially deployed app: VM Custom Script Extension failed to "
                            "compete within the specified timeout")

        self.vm_service.start_vm(compute_client, resource_group_name, vm_name)


    def power_off(self, compute_client, resource_group_name, vm_name):
        """Power off Azure VM instance

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param resource_group_name: The name of the resource group.
        :param vm_name: The name of the virtual machine.
        :return
        """
        self.vm_service.stop_vm(compute_client, resource_group_name, vm_name)
