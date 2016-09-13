from cloudshell.cp.azure.models.deploy_azure_vm_resource_model import DeployAzureVMResourceModel


class ResourceContextConverter(object):
    def __init__(self):
        pass

    def resource_context_to_deployment_resource_model(self, resource, deployment_credentials):
        """
        Converts a context to a deployment resource model

        :param resource : The context of the resource
        :param deployment_credentials:
        :return:
        """
        deployed_resource = DeployAzureVMResourceModel()
        deployed_resource.group_name = resource.attributes['AWS AMI Id']
        deployed_resource.vm_name = resource.attributes['AWS AMI Id']
        deployed_resource.cloud_provider = resource.attributes['AWS AMI Id']
        deployed_resource.instance_type = resource.attributes['AWS AMI Id']
        deployed_resource.wait_for_ip = resource.attributes['AWS AMI Id']
        deployed_resource.autoload = resource.attributes['AWS AMI Id']
        deployed_resource.add_public_ip = resource.attributes['AWS AMI Id']
        deployed_resource.inbound_ports = resource.attributes['AWS AMI Id']
        deployed_resource.outbound_ports = resource.attributes['AWS AMI Id']
        deployed_resource.public_ip_type = resource.attributes['AWS AMI Id']
        deployed_resource.image_publisher = resource.attributes['AWS AMI Id']
        deployed_resource.image_offer = resource.attributes['AWS AMI Id']
        deployed_resource.image_sku = resource.attributes['AWS AMI Id']
        deployed_resource.disk_type = resource.attributes['AWS AMI Id']
