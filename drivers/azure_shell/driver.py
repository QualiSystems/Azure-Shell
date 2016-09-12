from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface


class AzureShellDriver(ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        pass

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    def deploy_vm(self, context, request):
        pass

    def PowerOn(self, context, ports):
        pass

    def PowerOff(self, context, ports):
        pass

    def PowerCycle(self, context, ports, delay):
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        pass

    def destroy_vm_only(self, context, ports):
        pass

    def PrepareConnectivity(self, context, request):
        pass

    def CleanupConnectivity(self, context, request):
        pass

    def GetApplicationPorts(self, context, ports):
        pass

    def get_inventory(self, context):
        pass



