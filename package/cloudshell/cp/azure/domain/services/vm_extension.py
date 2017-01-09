from azure.mgmt.compute.models import OperatingSystemTypes
from azure.mgmt.compute.models import VirtualMachineExtension
from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error
from cloudshell.cp.azure.common.helpers.url_helper import URLHelper


class VMExtensionService(object):
    def __init__(self, url_helper, waiter_service):
        """

        :param cloudshell.cp.azure.common.helpers.url_helper.URLHelper url_helper:
        :param cloudshell.cp.azure.domain.services.task_waiter.TaskWaiterService waiter_service:
        :return:
        """
        self.waiter_service = waiter_service
        self.url_helper = url_helper

    WINDOWS_PUBLISHER = "Microsoft.Compute"
    WINDOWS_EXTENSION_TYPE = "CustomScriptExtension"
    WINDOWS_HANDLER_VERSION = "1.7"

    LINUX_PUBLISHER = "Microsoft.OSTCExtensions"
    LINUX_EXTENSION_TYPE = "CustomScriptForLinux"
    LINUX_HANDLER_VERSION = "1.5"

    def validate_script_extension(self, image_os_type, script_file, script_configurations):
        """Validate that script extension name and configuration are valid

        :param OperatingSystemTypes image_os_type: (enum) windows/linux value
        :param script_file: (str) path to the script file(s) that will be downloaded to the virtual machine
        :param script_configurations: (str) additional information for the extension execution
        :return:
        """
        if image_os_type is OperatingSystemTypes.windows:
            script_url = script_file.rstrip("/")

            if not script_url.endswith("ps1"):
                raise Exception("Invalid format for the PowerShell script. It must have a 'ps1' extension")
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
        file_uris = [file_uri.strip() for file_uri in script_file.split(",")]

        return VirtualMachineExtension(location=location,
                                       publisher=self.LINUX_PUBLISHER,
                                       type_handler_version=self.LINUX_HANDLER_VERSION,
                                       virtual_machine_extension_type=self.LINUX_EXTENSION_TYPE,
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
                                       publisher=self.WINDOWS_PUBLISHER,
                                       type_handler_version=self.WINDOWS_HANDLER_VERSION,
                                       virtual_machine_extension_type=self.WINDOWS_EXTENSION_TYPE,
                                       tags=tags,
                                       settings={
                                           "fileUris": [script_file],
                                           "commandToExecute": exec_command,
                                       })

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_script_extension(self, compute_client, location, group_name, vm_name, image_os_type, script_file,
                                script_configurations,timeout=1800, cancellation_context=None, tags=None):
        """Create VM Script extension on the Azure

        :param CancellationContext cancellation_context:
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

        # If the url is not valid we should stop the creation of the script
        if not self.url_helper.check_url(script_file):
            return False

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

        return self.waiter_service.wait_for_task_with_timeout(operation_poller=operation_poller,
                                                              cancellation_context=cancellation_context,
                                                              timeout=timeout)
