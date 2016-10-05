from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

from cloudshell.cp.azure.azure_shell import AzureShell


class AzureShellDriver(ResourceDriverInterface):
    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.azure_shell = AzureShell()
        self.azure_shell = None

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    def deploy_vm(self, context, request):
        azure_shell = self._get_azure_shell()
        return azure_shell.deploy_azure_vm(command_context=context, deployment_request=request)

    def PowerOn(self, context, ports):
        return self.azure_shell.power_on_vm(context)

    def PowerOff(self, context, ports):
        return self.azure_shell.power_off_vm(context)

    def PowerCycle(self, context, ports, delay):
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        pass

    def destroy_vm_only(self, context, ports):
        pass

    def PrepareConnectivity(self, context, request):
        return self._get_azure_shell().prepare_connectivity(context, request)

    def CleanupConnectivity(self, context, request):
        pass

    def GetApplicationPorts(self, context, ports):
        pass

    def get_inventory(self, context):
        pass

    def _get_azure_shell(self):
        """
        This is not a real singelton it's nice just for now ^_^
        :return: cloudshell.cp.azure.azure_shell.AzureShell
        """
        if self.azure_shell is None:
            self.azure_shell = AzureShell()
        return self.azure_shell
