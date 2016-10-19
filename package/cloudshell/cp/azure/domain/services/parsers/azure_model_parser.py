import jsonpickle
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel

from cloudshell.cp.azure.models.deploy_azure_vm_resource_model import DeployAzureVMResourceModel
from cloudshell.cp.azure.common.deploy_data_holder import DeployDataHolder
from cloudshell.cp.azure.models.reservation_model import ReservationModel


class AzureModelsParser(object):
    @staticmethod
    def convert_app_resource_to_deployed_app(resource):
        json_str = jsonpickle.decode(resource.app_context.deployed_app_json)
        data_holder = DeployDataHolder(json_str)
        return data_holder

    @staticmethod
    def convert_to_deployment_resource_model(deployment_request):
        data = jsonpickle.decode(deployment_request)
        data_holder = DeployDataHolder(data)
        deployment_resource_model = DeployAzureVMResourceModel()
        deployment_resource_model.add_public_ip = data_holder.ami_params.add_public_ip
        deployment_resource_model.autoload = data_holder.ami_params.autoload
        deployment_resource_model.cloud_provider = data_holder.ami_params.cloud_provider
        deployment_resource_model.disk_type = data_holder.ami_params.disk_type
        deployment_resource_model.group_name = data_holder.ami_params.group_name
        deployment_resource_model.image_offer = data_holder.ami_params.image_offer
        deployment_resource_model.image_publisher = data_holder.ami_params.image_publisher
        deployment_resource_model.image_sku = data_holder.ami_params.image_sku
        deployment_resource_model.inbound_ports = data_holder.ami_params.inbound_ports
        deployment_resource_model.instance_type = data_holder.ami_params.instance_type
        deployment_resource_model.outbound_ports = data_holder.ami_params.outbound_ports
        deployment_resource_model.public_ip_type = data_holder.ami_params.public_ip_type
        deployment_resource_model.vm_name = data_holder.ami_params.vm_name
        deployment_resource_model.wait_for_ip = data_holder.ami_params.wait_for_ip
        deployment_resource_model.app_name = data_holder.app_name

        return deployment_resource_model

    @staticmethod
    def convert_to_cloud_provider_resource_model(resource):
        """
        :param resource:
        :return: AzureCloudProviderResourceModel
        """
        resource_context = resource.attributes
        azure_resource_model = AzureCloudProviderResourceModel()
        azure_resource_model.azure_client_id = resource_context['Azure Client ID']
        azure_resource_model.azure_mgmt_network_d = resource_context['Azure Mgmt Network ID']
        azure_resource_model.azure_mgmt_nsg_id = resource_context['Azure Mgmt NSG ID']
        azure_resource_model.azure_mgmt_vnet = resource_context['Azure Mgmt VNET']
        azure_resource_model.azure_secret = resource_context['Azure Secret']
        azure_resource_model.azure_subscription_id = resource_context['Azure Subscription ID']
        azure_resource_model.azure_tenant = resource_context['Azure Tenant']
        azure_resource_model.instance_type = resource_context['Instance Type']
        azure_resource_model.keypairs_location = resource_context['Keypairs Location']
        azure_resource_model.networks_in_use = resource_context['Networks In Use']
        azure_resource_model.region = resource_context['Region']
        azure_resource_model.storage_type = resource_context['Storage Type']

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
            public_ip = resource_context.remote_endpoints[0].attributes.get("Public IP", public_ip)

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
