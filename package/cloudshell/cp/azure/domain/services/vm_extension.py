from azure.mgmt.compute.models import OperatingSystemTypes
from azure.mgmt.compute.models import VirtualMachineExtension


class VMExtensionService(object):
    def validate_script_extension(self, image_os_type, script_file, script_configurations):
        """Validate that script extension name and configuration are valid

        :param image_os_type: (enum) azure.mgmt.compute.models.OperatingSystemTypes windows/linux value
        :param script_file: (str) path to the script file(s) that will be downloaded to the virtual machine
        :param script_configurations: (str) additional information for the extension execution
        :return:
        """
        if image_os_type is OperatingSystemTypes.windows:
            script_url = script_file.rstrip("/")

            if not script_url.endswith("ps1"):
                # todo: check error here from azure
                raise Exception("Not valid")
        else:
            if not script_configurations:
                raise Exception("Linux Custom Script must have a command to execute in "
                                "'Extension Script Configurations' attribute")

    def _prepare_linux_vm_script_extension(self, location, script_file, script_configurations, tags):
        """Prepare VirtualMachineExtension model for Linux custom script extension

        :param location: (str) Azure region
        :param script_file: (str) path to the script file(s) that will be downloaded to the virtual machine
        :param script_configurations: (str) additional information for the extension execution
        :param tags: (dict) Azure tags
        :return: azure.mgmt.compute.models.VirtualMachineExtension instance
        """
        # TODO: ADD RETRIES !!!
        file_uris = [file_uri.strip() for file_uri in script_file.split(",")]
        return VirtualMachineExtension(location=location,
                                       publisher="Microsoft.OSTCExtensions",
                                       type_handler_version="1.5",
                                       virtual_machine_extension_type="CustomScriptForLinux",
                                       tags=tags,
                                       settings={
                                           "fileUris": file_uris,
                                           "commandToExecute": script_configurations,
                                       })

    def _prepare_windows_vm_script_extension(self, location, script_file, script_configurations, tags):
        """Prepare VirtualMachineExtension model for Windows PowerShell script extension

        :param location: (str) Azure region
        :param script_file:
        :param script_configurations:
        :param tags: (dict) Azure tags
        :return: azure.mgmt.compute.models.VirtualMachineExtension instance
        """
        file_name = script_file.rstrip("/").split("/")[-1]
        exec_command = "powershell.exe -ExecutionPolicy Unrestricted -File {} {}".format(
            file_name, script_configurations)

        return VirtualMachineExtension(location=location,
                                       publisher="Microsoft.Compute",
                                       type_handler_version="1.7",
                                       virtual_machine_extension_type="CustomScriptExtension",
                                       tags=tags,
                                       settings={
                                           "fileUris": [script_file],
                                           "commandToExecute": exec_command,
                                       })

    def create_script_extension(self, compute_client, location, group_name, vm_name, image_os_type, script_file,
                                script_configurations, tags=None):
        """Create VM Script extension on the Azure

        :param compute_client: azure.mgmt.compute.compute_management_client.ComputeManagementClient instance
        :param location: (str) Azure region
        :param group_name: (str) the name of the resource group on Azure
        :param vm_name: (str) name of the virtual machine
        :param image_os_type: (enum) azure.mgmt.compute.models.OperatingSystemTypes windows/linux value
        :param script_file: (str) path to the script file(s) that will be downloaded to the virtual machine
        :param script_configurations: (str) additional information for the extension execution
        :param tags: (dict) Azure tags
        :return:
        """
        if image_os_type is OperatingSystemTypes.linux:
            vm_extension = self._prepare_linux_vm_script_extension(location=location,
                                                                   script_file=script_file,
                                                                   script_configurations=script_configurations,
                                                                   tags=tags)
        else:
            vm_extension = self._prepare_windows_vm_script_extension(location=location,
                                                                     script_file=script_file,
                                                                     script_configurations=script_configurations,
                                                                     tags=tags)

        operation_poller = compute_client.virtual_machine_extensions.create_or_update(
            resource_group_name=group_name,
            vm_name=vm_name,
            vm_extension_name=vm_name,
            extension_parameters=vm_extension)

        return operation_poller.result()
