from cloudshell.cp.azure.azure_shell import AzureShell
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface




class AllDeployments(object):
    def __init__(self, some_data):
        self.some_data = some_data

    def deploy(self, requset=None, context=None, cancelation_context=None):
        pass
        # with LoggingSessionContext(context) as logger:
        #     with ErrorHandlingContext(logger):
        #         with CloudShellSessionContext(context) as session:
        #             logger.info('Deploy started')
        #
        #             # create deployment resource model and serialize it to json
        #             azure_vm_deployment_model = (
        #                 self.resource_context_converter.resource_context_to_deploy_azure_vm_model(context.resource, ''))
        #
        #             app_request = jsonpickle.decode(context.resource.app_context.app_request_json)
        #
        #             vm_res_name = app_request['name']
        #             cloud_provider_name = app_request["deploymentService"].get("cloudProviderName")
        #
        #             if cloud_provider_name:
        #                 azure_vm_deployment_model.cloud_provider = str(cloud_provider_name)
        #
        #             deployment_info = self.deployment_helper.get_deployment_info(azure_vm_deployment_model, vm_res_name)
        #
        #             # Calls command on the Azure Cloud Provider
        #             result = session.ExecuteCommand(context.reservation.reservation_id,
        #                                             azure_vm_deployment_model.cloud_provider,
        #                                             "Resource",
        #                                             "deploy_vm",
        #                                             self.deployment_helper.get_command_inputs_list(deployment_info),
        #                                             False)
        #
        #             return self.deployment_helper.process_command_execution_result(logger=logger, result=result)

        # wow im doing some deploy stuff here!
        #


    def deploy2(self, requset=None, context=None, cancelation_context=None):
        pass


class AzureShellDriver(ResourceDriverInterface):
    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        all_deployments = AllDeployments("some data")
        self.deployments = dict()
        self.deployments['Deploy Azure VM'] = all_deployments.deploy
        self.deployments['Deploy Azure VM 2'] = all_deployments.deploy2
        self.azure_shell = AzureShell()

    def Deploy(self, context, Name=None, request=None, cancelation_context=None):
        deployment_name =request.deployment_name
        if deployment_name in self.deployments.keys():
            deploy_method = self.deployments[deployment_name]
            deploy_method(request)
        else:
            raise Exception('Could not find the deployment')

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

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
        return self.azure_shell.cleanup_connectivity(command_context=context)

    def GetApplicationPorts(self, context, ports):
        return self.azure_shell.get_application_ports(command_context=context)

    def get_inventory(self, context):
        return self.azure_shell.get_inventory(command_context=context)

    def GetAccessKey(self, context, ports):
        return self.azure_shell.get_access_key(context)
