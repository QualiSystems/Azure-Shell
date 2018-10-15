import jsonpickle
from cloudshell.cp.azure.azure_shell import AzureShell
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

class AzureShellDriver(ResourceDriverInterface):
    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.deployments = dict()
        self.deployments['Azure VM From Marketplace'] = self.deploy_vm
        self.deployments['Azure VM From Custom Image'] = self.deploy_vm_from_custom_image
        self.azure_shell = AzureShell()

    def Deploy(self, context, request=None, cancellation_context=None):
        app_request = jsonpickle.decode(request)
        deployment_name = app_request['DeploymentServiceName']
        if deployment_name in self.deployments.keys():
            deploy_method = self.deployments[deployment_name]
            return deploy_method(context,request,cancellation_context)
        else:
            raise Exception('Could not find the deployment')

    def initialize(self, context):
        pass

    def cleanup(self):  
        pass

    def create_route_table(self,context,request):
        """ Creates a route table, as well as routes and associates it with whatever subnets are relevant
        Example route table request:
        {
            "subnets": ["subnet1", "subnet2"],
            "routes": [{
                            "name":                 "myRoute1",
                            "address_prefix":       "10.0.1.0/28" # cidr
                            "next_hop_type":        "VirtualAppliance"
                            "next_hop_address":     "10.0.1.15"
            }]


        """
        return self.azure_shell.create_route_table(context,request)

    def deploy_vm(self, context, request, cancellation_context):
        return self.azure_shell.deploy_azure_vm(command_context=context,
                                                deployment_request=request,
                                                cancellation_context=cancellation_context)

    def deploy_vm_from_custom_image(self, context, request, cancellation_context):
        return self.azure_shell.deploy_vm_from_custom_image(command_context=context,
                                                            deployment_request=request,
                                                            cancellation_context=cancellation_context)

    def PowerOn(self, context, ports):
        return self.azure_shell.power_on_vm(context)

    def PowerOff(self, context, ports):
        return self.azure_shell.power_off_vm(context)

    def PowerCycle(self, context, ports, delay):
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        return self.azure_shell.refresh_ip(context)

    def destroy_vm_only(self, context, ports):
        self.azure_shell.delete_azure_vm(command_context=context)

    def PrepareConnectivity(self, context, request, cancellation_context):
        return self.azure_shell.prepare_connectivity(context, request, cancellation_context)

    def CleanupConnectivity(self, context, request):
        return self.azure_shell.cleanup_connectivity(command_context=context, request=request)

    def GetApplicationPorts(self, context, ports):
        return self.azure_shell.get_application_ports(command_context=context)

    def get_inventory(self, context):
        return self.azure_shell.get_inventory(command_context=context)

    def GetAccessKey(self, context, ports):
        return self.azure_shell.get_access_key(context)

    def SetAppSecurityGroups(self, context, request):
        return self.azure_shell.set_app_security_groups(context, request)

    def GetVmDetails(self, context, cancellation_context, requests):
        return self.azure_shell.get_vm_details(context, cancellation_context, requests)



