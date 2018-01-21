import jsonpickle

from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMFromCustomImageResourceModel
from cloudshell.cp.azure.common.deploy_data_holder import DeployDataHolder
from cloudshell.cp.azure.models.reservation_model import ReservationModel




class AzureModelsParser(object):
    @staticmethod
    def convert_app_resource_to_deployed_app(resource):
        json_str = jsonpickle.decode(resource.app_context.deployed_app_json)
        data_holder = DeployDataHolder(json_str)
        return data_holder

    @staticmethod
    def convert_app_resource_to_request(resource):
        json_str = jsonpickle.decode(resource.app_context.app_request_json)
        data_holder = DeployDataHolder(json_str)
        return data_holder

    @staticmethod
    def _set_base_deploy_azure_vm_model_params(deployment_resource_model, data_holder, cloudshell_session, logger):
        """
        Set base parameters to the Azure Deploy model

        :param deployment_resource_model: deploy_azure_vm_resource_models.BaseDeployAzureVMResourceModel subclass
        :param data_holder: DeployDataHolder instance
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session: instance
        :param logging.Logger logger:
        """

        data_attributes = data_holder['Attributes']
        deployment_resource_model.add_public_ip = AzureModelsParser.convert_to_boolean(data_attributes['Add Public IP'])
        deployment_resource_model.autoload = AzureModelsParser.convert_to_boolean(data_attributes['Autoload'])
        deployment_resource_model.inbound_ports = data_attributes['Inbound Ports']
        deployment_resource_model.vm_size = data_attributes['VM Size']
        deployment_resource_model.public_ip_type = data_attributes['Public IP Type']
        deployment_resource_model.extension_script_file = data_attributes['Extension Script file']
        deployment_resource_model.extension_script_configurations = data_attributes['Extension Script Configurations']
        deployment_resource_model.extension_script_timeout = (int(data_attributes['Extension Script Timeout']))
        deployment_resource_model.disk_type = data_attributes['Disk Type']
        deployment_resource_model.app_name = data_holder['AppName']
        logical_resource = data_holder['LogicalResourceRequestAttributes']

        keys = logical_resource.keys()

        username_key = 'User'
        deployment_resource_model.username = logical_resource[username_key] if username_key in keys else None

        password_key = 'Password'
        deployment_resource_model.password = logical_resource[password_key] if password_key in keys else None

        if deployment_resource_model.password:
            logger.info('Decrypting Azure VM password...')
            decrypted_pass = cloudshell_session.DecryptPassword(deployment_resource_model.password)
            deployment_resource_model.password = decrypted_pass.Value
        return deployment_resource_model

    @staticmethod
    def convert_to_boolean( value):
        return value.lower() in ['1', 'true']

    @staticmethod
    def _convert_list_attribute(attribute):
        """Convert string attribute "param1, param2, param3" into list ["param1", "param2", "param3"]

        :param str attribute: data model attribute
        :return: attribute list of params
        :rtype: list
        """
        if attribute:
            list_attr = [param.strip() for param in attribute.split(",")]
        else:
            list_attr = []

        return list_attr

    @staticmethod
    def convert_to_deploy_azure_vm_resource_model(deployment_request, cloudshell_session, logger):
        """
        Convert deployment request JSON to the DeployAzureVMResourceModel model

        :param str deployment_request: JSON string
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session: instance
        :param logging.Logger logger:
        :return: deploy_azure_vm_resource_models.DeployAzureVMResourceModel instance
        :rtype: DeployAzureVMResourceModel
        """
        data = jsonpickle.decode(deployment_request)
        deployment_resource_model = DeployAzureVMResourceModel()
        data_attributes = data['Attributes']
        deployment_resource_model.image_offer = data_attributes['Image Offer']
        deployment_resource_model.image_publisher = data_attributes['Image Publisher']
        deployment_resource_model.image_sku = data_attributes['Image SKU']
        deployment_resource_model.image_version = data_attributes['Image Version']
        AzureModelsParser._set_base_deploy_azure_vm_model_params(deployment_resource_model=deployment_resource_model,
                                                                 data_holder=data,
                                                                 cloudshell_session=cloudshell_session,
                                                                 logger=logger)

        return deployment_resource_model

    @staticmethod
    def convert_to_deploy_azure_vm_from_custom_image_resource_model(deployment_request, cloudshell_session, logger):
        """
        Convert deployment request JSON to the DeployAzureVMFromCustomImageResourceModel model

        :param str deployment_request: JSON string
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session: instance
        :param logging.Logger logger:
        :return: deploy_azure_vm_resource_models.DeployAzureVMFromCustomImageResourceModel instance
        :rtype: DeployAzureVMFromCustomImageResourceModel
        """
        data = jsonpickle.decode(deployment_request)
        data_attributes = data['Attributes']
        deployment_resource_model = DeployAzureVMFromCustomImageResourceModel()
        deployment_resource_model.image_name = data_attributes['Azure Image']
        deployment_resource_model.image_resource_group = data_attributes['Azure Resource Group']
        AzureModelsParser._set_base_deploy_azure_vm_model_params(deployment_resource_model=deployment_resource_model,
                                                                 data_holder=data,
                                                                 cloudshell_session=cloudshell_session,
                                                                 logger=logger)

        AzureModelsParser.validate_custom_image_model(deployment_resource_model)

        return deployment_resource_model

    @staticmethod
    def validate_custom_image_model(model):
        """
        :param DeployAzureVMFromCustomImageResourceModel model:
        :return:
        """
        if not model.image_name:
            raise ValueError("Azure Image attribute is mandatory and cannot be empty")

        if not model.image_resource_group:
            raise ValueError("Azure Resource Group attribute is mandatory and cannot be empty")

    @staticmethod
    def convert_to_cloud_provider_resource_model(resource, cloudshell_session):
        """
        :param resource:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session: instance
        :return: AzureCloudProviderResourceModel
        """
        resource_context = resource.attributes
        azure_resource_model = AzureCloudProviderResourceModel()
        azure_resource_model.azure_application_id = resource_context['Azure Application ID']
        azure_resource_model.azure_subscription_id = resource_context['Azure Subscription ID']
        azure_resource_model.azure_tenant = resource_context['Azure Tenant ID']
        azure_resource_model.vm_size = resource_context['VM Size']
        azure_resource_model.region = resource_context['Region'].replace(" ", "").lower()
        azure_resource_model.management_group_name = resource_context['Management Group Name']

        azure_resource_model.networks_in_use = AzureModelsParser._convert_list_attribute(
            resource_context['Networks In Use'])

        azure_resource_model.additional_mgmt_networks = AzureModelsParser._convert_list_attribute(
            resource_context['Additional Mgmt Networks'])

        encrypted_azure_application_key = resource_context['Azure Application Key']
        azure_application_key = cloudshell_session.DecryptPassword(encrypted_azure_application_key)
        azure_resource_model.azure_application_key = azure_application_key.Value

        return azure_resource_model

    @staticmethod
    def convert_to_reservation_model(reservation_context):
        """
        :param ReservationContextDetails reservation_context:
        :rtype: ReservationModel
        """
        return ReservationModel(reservation_context)

    @staticmethod
    def get_public_ip_from_connected_resource_details(resource_context):
        public_ip = ""
        if resource_context.remote_endpoints is not None:
            attributes = resource_context.remote_endpoints[0].attributes
            public_ip = AzureModelsParser.get_attribute_value_by_name_ignoring_namespace(attributes, "Public IP")

        return public_ip

    @staticmethod
    def get_private_ip_from_connected_resource_details(resource_context):
        private_ip = ""
        if resource_context.remote_endpoints is not None:
            private_ip = resource_context.remote_endpoints[0].address

        return private_ip

    @staticmethod
    def get_connected_resource_fullname(resource_context):
        if resource_context.remote_endpoints[0]:
            return resource_context.remote_endpoints[0].fullname
        else:
            raise ValueError('Could not find resource fullname on the deployed app.')

    @staticmethod
    def get_attribute_value_by_name_ignoring_namespace(attributes, name):
        """
        Finds the attribute value by name ignoring attribute namespaces.
        :param dict attributes: Attributes key value dict to search on.
        :param str name: Attribute name to search for.
        :return: Attribute str value. None if not found.
        :rtype: str
        """
        for key, val in attributes.iteritems():
            last_part = key.split(".")[-1]  # get last part of namespace.
            if name == last_part:
                return val
        return None


