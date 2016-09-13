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
        raise Exception("this is an exception from  resource_context_to_deployment_resource_model")


        # deployedResource = DeployAWSEc2AMIInstanceResourceModel()
        # deployedResource.aws_ami_id = resource.attributes['AWS AMI Id']
        # deployedResource.cloud_provider = resource.attributes['Cloud Provider']
        # deployedResource.storage_iops = resource.attributes['Storage IOPS']
        # deployedResource.storage_size = resource.attributes['Storage Size']
        # deployedResource.storage_type = resource.attributes['Storage Type']
        # deployedResource.instance_type = resource.attributes['Instance Type']
        # deployedResource.wait_for_ip = resource.attributes['Wait for IP']
        # deployedResource.autoload = resource.attributes['Autoload']
        # deployedResource.inbound_ports = resource.attributes['Inbound Ports']
        # deployedResource.outbound_ports = resource.attributes['Outbound Ports']
        # deployedResource.wait_for_credentials = self._convert_to_bool(resource.attributes['Wait for Credentials'])
        # deployedResource.add_public_ip = self._convert_to_bool(resource.attributes['Add Public IP'])
        # deployedResource.add_elastic_ip = resource.attributes['Add Elastic IP']
        # deployedResource.root_volume_name = resource.attributes['Root Volume Name']
        # deployedResource.user = deployment_credentiales['user']
        # deployedResource.wait_for_status_check = resource.attributes['Wait for Status Check']
