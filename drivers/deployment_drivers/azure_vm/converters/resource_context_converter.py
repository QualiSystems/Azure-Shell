import jsonpickle

from cloudshell.cp.azure.models.deploy_azure_vm_resource_model import DeployAzureVMResourceModel


class ResourceContextConverter(object):
    def __init__(self):
        pass

    def _get_attribute_by_name(self, attr_name, attrs):
        """Get attribute value by it's name from the attributes list

        :param attr_name: str name of the attribute
        :param attrs: list of attribute dictionaries: [{"name": "some_attr", "value": "some_value"}, ...]
        :return:
        """
        return next(attr["value"] for attr in attrs if attr["name"] == attr_name)

    def resource_context_to_deployment_resource_model(self, resource, deployment_credentials):
        """
        Converts a context to a deployment resource model

        :param resource : The context of the resource
        :param deployment_credentials:
        :return:
        """
        deployed_resource = DeployAzureVMResourceModel()
        deployed_resource.group_name = ""  # needs to be auto generated
        deployed_resource.vm_name = ""  # needs to be auto generated
        deployed_resource.cloud_provider = resource.attributes['Cloud Provider']
        deployed_resource.instance_type = resource.attributes['Instance Type']
        deployed_resource.wait_for_ip = resource.attributes['Wait for IP']
        deployed_resource.autoload = resource.attributes['Autoload']
        deployed_resource.add_public_ip = resource.attributes['Add Public IP']
        deployed_resource.inbound_ports = resource.attributes['Inbound Ports']
        deployed_resource.outbound_ports = resource.attributes['Outbound Ports']
        deployed_resource.public_ip_type = resource.attributes['Public IP Type']
        deployed_resource.image_publisher = resource.attributes['Image Publisher']
        deployed_resource.image_offer = resource.attributes['Image Offer']
        deployed_resource.image_sku = resource.attributes['Image SKU']
        deployed_resource.disk_type = resource.attributes['Disk Type']

        app_request = jsonpickle.decode(resource.app_context.app_request_json)
        attrs = app_request["logicalResource"]["attributes"]
        deployed_resource.username = self._get_attribute_by_name("User", attrs)
        deployed_resource.password = self._get_attribute_by_name("Password", attrs)

        return deployed_resource
