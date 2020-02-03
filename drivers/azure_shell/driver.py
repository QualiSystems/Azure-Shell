from cloudshell.cp.azure.azure_shell import AzureShell
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.cp.core import DriverRequestParser
from cloudshell.cp.core.models import DeployApp, DriverResponse
from cloudshell.cp.core.utils import single



class AzureShellDriver(ResourceDriverInterface):
    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.request_parser = DriverRequestParser()
        self.deployments = dict()
        self.deployments['Azure VM From Marketplace'] = self.deploy_vm
        self.deployments['Azure VM From Custom Image'] = self.deploy_vm_from_custom_image
        self.azure_shell = AzureShell()

    def Deploy(self, context, request=None, cancellation_context=None):
        actions = self.request_parser.convert_driver_request_to_actions(request)
        deploy_action = single(actions, lambda x: isinstance(x, DeployApp))

        deployment_name = deploy_action.actionParams.deployment.deploymentPath

        if deployment_name in self.deployments.keys():
            deploy_method = self.deployments[deployment_name]
            results = deploy_method(context, actions, cancellation_context)
            return DriverResponse(results).to_driver_response_json()
        else:
            raise Exception('Could not find the deployment')

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    def deploy_vm(self, context, actions, cancellation_context):
        return self.azure_shell.deploy_azure_vm(command_context=context,
                                                actions=actions,
                                                cancellation_context=cancellation_context)

    def CreateRouteTables(self, context, request):
        return self.azure_shell.create_route_tables(context, request)

    def deploy_vm_from_custom_image(self, context, actions, cancellation_context):
        return self.azure_shell.deploy_vm_from_custom_image(command_context=context,
                                                            actions=actions,
                                                            cancellation_context=cancellation_context)

    def PowerOn(self, context, ports):
        return self.azure_shell.power_on_vm(context)

    def PowerOff(self, context, ports):
        return self.azure_shell.power_off_vm(context)

    def PowerCycle(self, context, ports, delay):
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        return self.azure_shell.refresh_ip(context)

    def DeleteInstance(self, context, ports):
        self.azure_shell.delete_azure_vm(command_context=context)

    def PrepareSandboxInfra(self, context, request, cancellation_context):
        actions = self.request_parser.convert_driver_request_to_actions(request)
        results = self.azure_shell.prepare_connectivity(context, actions, cancellation_context)
        return DriverResponse(results).to_driver_response_json()

    def CleanupSandboxInfra(self, context, request):
        return self.azure_shell.cleanup_connectivity(command_context=context, request=request)

    def GetApplicationPorts(self, context, ports):
        return self.azure_shell.get_application_ports(command_context=context)

    def get_inventory(self, context):
        return self.azure_shell.get_inventory(command_context=context)

    def GetAccessKey(self, context, ports):
        return self.azure_shell.get_access_key(context)

    def GetVmDetails(self, context, cancellation_context, requests):
        return self.azure_shell.get_vm_details(context, cancellation_context, requests)

    def SetAppSecurityGroups(self, context, request):
        return self.azure_shell.set_app_security_groups(context, request)

    def GetAvailablePrivateIP(self, context, subnet_cidr, owner):
        return self.azure_shell.get_available_private_ip(context, subnet_cidr, owner)
