from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

from cloudshell.cp.azure.azure_shell import AzureShell


class AzureShellDriver(ResourceDriverInterface):
    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.azure_shell = AzureShell()

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    def deploy_vm(self, context, request):
        return self.azure_shell.deploy_azure_vm(command_context=context, deployment_request=request)

    def PowerOn(self, context, ports):
        return self.azure_shell.power_on_vm(context)

    def PowerOff(self, context, ports):
        return self.azure_shell.power_off_vm(context)

    def PowerCycle(self, context, ports, delay):
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        pass

    def destroy_vm_only(self, context, ports):
        self.azure_shell.delete_azure_vm(command_context=context)

    def PrepareConnectivity(self, context, request):
        pass

    def CleanupConnectivity(self, context, request):
        self.azure_shell.cleanup_connectivity(command_context=context)

    def GetApplicationPorts(self, context, ports):
        pass

    def get_inventory(self, context):
        pass
