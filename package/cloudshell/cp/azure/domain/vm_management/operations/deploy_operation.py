import uuid

import jsonpickle
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.models.deploy_result_model import DeployResult


class DeployAzureVMOperation(object):
    def __init__(self,
                 logger,
                 vm_service):
        """

        :param logger:
        :param VirtualMachineService vm_service:
        :return:
        """

        self.logger = logger
        self.vm_service = vm_service

    def deploy(self, azure_vm_deployment_model, cloud_provider_model, reservation_id):
        """
        :param reservation_id:
        :param cloudshell.cp.azure.models.deploy_azure_vm_resource_model.DeployAzureVMResourceModel azure_vm_deployment_model:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :return:
        """
        base_name = "quali"
        resource_name = azure_vm_deployment_model.app_name # self._generate_name(azure_vm_deployment_model.app_name)
        random_name = self._generate_name(base_name)
        group_name = str(reservation_id)
        interface_name = random_name
        network_name = base_name
        subnet_name = base_name
        ip_name = random_name
        storage_account_name = base_name
        computer_name = random_name
        admin_username = resource_name
        admin_password = 'ScJaw12deDFG'
        vm_name = random_name

        # 1. Crate a resource group
        self.vm_service.create_group(group_name=group_name, region=cloud_provider_model.region)

        # 2. Create a storage account
        self.vm_service.create_storage_account(group_name=group_name,
                                               region=cloud_provider_model.region,
                                               storage_account_name=storage_account_name)

        # 3. Create the network interface
        nic_id = self.vm_service.create_network(group_name=group_name,
                                                interface_name=interface_name,
                                                ip_name=ip_name,
                                                network_name=network_name,
                                                region=cloud_provider_model.region,
                                                subnet_name=subnet_name)

        # 4. create Vm
        result_create = self.vm_service.create_vm(image_offer=azure_vm_deployment_model.image_offer,
                                  image_publisher=azure_vm_deployment_model.image_publisher,
                                  image_sku=azure_vm_deployment_model.image_sku,
                                  image_version='latest',
                                  admin_password=admin_password,
                                  admin_username=admin_username,
                                  computer_name=computer_name,
                                  group_name=group_name,
                                  nic_id=nic_id,
                                  region=cloud_provider_model.region,
                                  storage_name=storage_account_name,
                                  vm_name=vm_name)

        vm = self.vm_service.get_vm(group_name=group_name, vm_name=vm_name)

        deployed_app_attributes = self._prepare_deployed_app_attributes(admin_username, admin_password, "TBD")

        return DeployResult(vm_name=vm_name,
                            vm_uuid=result_create.vm_id,
                            cloud_provider_resource_name=azure_vm_deployment_model.cloud_provider,
                            auto_power_off=True,
                            wait_for_ip=azure_vm_deployment_model.wait_for_ip,
                            auto_delete=True,
                            autoload=azure_vm_deployment_model.autoload,
                            inbound_ports=azure_vm_deployment_model.inbound_ports,
                            outbound_ports=azure_vm_deployment_model.outbound_ports,
                            deployed_app_attributes=deployed_app_attributes,
                            deployed_app_address="10.10.10.10",
                            public_ip="10.10.10.11")

    @staticmethod
    def _generate_name(name):
        return name.replace(" ", "") + ((str(uuid.uuid4())).replace("-", ""))[0:8]

    @staticmethod
    def _prepare_deployed_app_attributes(admin_username, admin_password, public_ip):
        """

        :param admin_username:
        :param admin_password:
        :param public_ip:
        :return: dict
        """

        deployed_app_attr = {'Password': admin_password, 'User': admin_username, 'Public IP': public_ip}

        return deployed_app_attr
