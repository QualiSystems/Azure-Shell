import jsonpickle
from cloudshell.cp.core.utils import first_or_default
from typing import List

from cloudshell.cp.azure.common.parsers.security_group_parser import SecurityGroupParser
from cloudshell.cp.azure.domain.services.parsers.network_actions import NetworkActionsParser
from cloudshell.cp.azure.models.app_security_groups_model import AppSecurityGroupModel, DeployedApp, VmDetails
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMResourceModel, \
    RouteTableRequestResourceModel, RouteResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMFromCustomImageResourceModel
from cloudshell.cp.azure.common.deploy_data_holder import DeployDataHolder
from cloudshell.cp.azure.models.reservation_model import ReservationModel
from cloudshell.cp.azure.domain.services.parsers.connection_params import convert_to_bool


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
    def _set_base_deploy_azure_vm_model_params(deployment_resource_model, deploy_action, network_actions, cloudshell_session, logger):
        """
        Set base parameters to the Azure Deploy model

        :param deployment_resource_model: deploy_azure_vm_resource_models.BaseDeployAzureVMResourceModel subclass
        :param data_holder: DeployDataHolder instance
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session: instance
        :param logging.Logger logger:
        """

        data_attributes = deploy_action.actionParams.deployment.attributes
        deployment_resource_model.add_public_ip = AzureModelsParser.convert_to_boolean(data_attributes['Add Public IP'])
        deployment_resource_model.autoload = AzureModelsParser.convert_to_boolean(data_attributes['Autoload'])
        deployment_resource_model.inbound_ports = data_attributes['Inbound Ports']
        deployment_resource_model.vm_size = data_attributes['VM Size']
        deployment_resource_model.disk_size = data_attributes['Disk Size']
        deployment_resource_model.public_ip_type = data_attributes['Public IP Type']
        deployment_resource_model.extension_script_file = data_attributes['Extension Script file']
        deployment_resource_model.extension_script_configurations = data_attributes['Extension Script Configurations']
        deployment_resource_model.extension_script_timeout = (int(data_attributes['Extension Script Timeout']))
        deployment_resource_model.disk_type = data_attributes['Disk Type']
        deployment_resource_model.allow_all_sandbox_traffic = data_attributes['Allow all Sandbox Traffic']
        deployment_resource_model.app_name = deploy_action.actionParams.appName
        logical_resource = deploy_action.actionParams.appResource.attributes  # its not a dictionary!!?@@#@!?#

        keys = logical_resource.keys()

        username_key = 'User'
        full_username_key = first_or_default(keys, AzureModelsParser._gen2_attributes_lambda(username_key))
        deployment_resource_model.username = logical_resource[full_username_key] if full_username_key else None

        password_key = 'Password'
        full_password_key = first_or_default(keys, AzureModelsParser._gen2_attributes_lambda(password_key))
        deployment_resource_model.password = logical_resource[full_password_key] if full_password_key else None

        if deployment_resource_model.password:
            logger.info('Decrypting Azure VM password...')
            decrypted_pass = cloudshell_session.DecryptPassword(deployment_resource_model.password)
            deployment_resource_model.password = decrypted_pass.Value

        deployment_resource_model.network_configurations = \
            AzureModelsParser.parse_deploy_networking_configurations(network_actions,logger)

        return deployment_resource_model

    @staticmethod
    def _gen2_attributes_lambda(attribute_key):
        return lambda x: x == attribute_key or x.endswith("." + attribute_key)

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
    def convert_to_route_table_model(route_table_request):
        """
        Convert deployment request JSON to the DeployAzureVMResourceModel model

        :param str deployment_request: JSON string
        :return: deploy_azure_vm_resource_models.DeployAzureVMResourceModel instance
        :rtype: list[RouteTableRequestResourceModel]
        """
        data = jsonpickle.decode(route_table_request)
        route_table_models = []
        for route_table in data['route_tables']:
            route_table_model = RouteTableRequestResourceModel()
            route_table_model.name = route_table['name']
            route_table_model.subnets = []
            if route_table['subnets']:
                route_table_model.subnets = route_table['subnets']
            routes = []
            for route in route_table['routes']:
                route_model = RouteResourceModel()
                route_model.name = route['name']
                route_model.route_address_prefix = route['address_prefix']
                route_model.next_hop_type = route['next_hop_type']
                route_model.next_hope_address = route['next_hop_address']
                routes.append(route_model)
            route_table_model.routes = routes

            route_table_models.append(route_table_model)

        return route_table_models

    @staticmethod
    def convert_to_deploy_azure_vm_resource_model(deploy_action, network_actions, cloudshell_session, logger):
        """
        Convert deployment request JSON to the DeployAzureVMResourceModel model

        :param package.cloudshell.cp.core.models.DeployApp deploy_action: describes the desired deployment
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session: instance
        :param logging.Logger logger:
        :return: deploy_azure_vm_resource_models.DeployAzureVMResourceModel instance
        :rtype: DeployAzureVMResourceModel
        """
        deployment_resource_model = DeployAzureVMResourceModel()
        data_attributes = deploy_action.actionParams.deployment.attributes
        deployment_resource_model.image_offer = data_attributes['Image Offer']
        deployment_resource_model.image_publisher = data_attributes['Image Publisher']
        deployment_resource_model.image_sku = data_attributes['Image SKU']
        deployment_resource_model.image_version = data_attributes['Image Version']
        AzureModelsParser._set_base_deploy_azure_vm_model_params(deployment_resource_model=deployment_resource_model,
                                                                 deploy_action=deploy_action,
                                                                 network_actions=network_actions,
                                                                 cloudshell_session=cloudshell_session,
                                                                 logger=logger)

        return deployment_resource_model

    @staticmethod
    def convert_to_deploy_azure_vm_from_custom_image_resource_model(deploy_action, network_actions, cloudshell_session, logger):
        """
        Convert deployment request JSON to the DeployAzureVMFromCustomImageResourceModel model

        :param package.cloudshell.cp.core.models.DeployApp deploy_action: describes the desired deployment
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session: instance
        :param logging.Logger logger:
        :return: deploy_azure_vm_resource_models.DeployAzureVMFromCustomImageResourceModel instance
        :rtype: DeployAzureVMFromCustomImageResourceModel
        """
        data_attributes = deploy_action.actionParams.deployment.attributes
        deployment_resource_model = DeployAzureVMFromCustomImageResourceModel()
        deployment_resource_model.image_name = data_attributes['Azure Image']
        deployment_resource_model.image_resource_group = data_attributes['Azure Resource Group']
        AzureModelsParser._set_base_deploy_azure_vm_model_params(deployment_resource_model=deployment_resource_model,
                                                                 deploy_action=deploy_action,
                                                                 network_actions=network_actions,
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
        azure_resource_model.private_ip_allocation_method = resource_context["Private IP Allocation Method"]

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

    @staticmethod
    def parse_deploy_networking_configurations(actions, logger):
        """
        :param deployment_request: request object to parse
        :return:
        """
        logger.warn('here')
        if not actions:
            return None
        # actions = deployment_request["NetworkConfigurationsRequest"]

        return NetworkActionsParser.parse_network_actions_data(actions,logger)

    @staticmethod
    def get_app_security_groups_from_request(request):
        json_str = jsonpickle.decode(request)
        data_holder = DeployDataHolder.create_obj_by_type(json_str)
        return data_holder

    @staticmethod
    def convert_to_app_security_group_models(request):
        """
        :rtype List[AppSecurityGroupModel]:
        """
        security_group_models = []

        security_groups = AzureModelsParser.get_app_security_groups_from_request(request)

        for security_group in security_groups:
            security_group_model = AppSecurityGroupModel()
            security_group_model.deployed_app = DeployedApp()
            security_group_model.deployed_app.name = security_group.deployedApp.name
            security_group_model.deployed_app.vm_details = VmDetails()
            security_group_model.deployed_app.vm_details.uid = security_group.deployedApp.vmdetails.uid
            security_group_model.security_group_configurations = SecurityGroupParser.parse_security_group_configurations(
                security_group.securityGroupsConfigurations)

            security_group_models.append(security_group_model)

        return security_group_models

    @staticmethod
    def get_allow_all_storage_traffic_from_connected_resource_details(resource_context):
        allow_traffic_on_resource = ""
        allow_all_storage_traffic = 'Allow all Sandbox Traffic'
        if resource_context.remote_endpoints is not None:
            data = jsonpickle.decode(resource_context.remote_endpoints[0].app_context.app_request_json)
            attributes = {d["name"]: d["value"] for d in data["deploymentService"]["attributes"]}
            allow_traffic_on_resource = AzureModelsParser.get_attribute_value_by_name_ignoring_namespace(
                attributes, allow_all_storage_traffic)
        return allow_traffic_on_resource
