import uuid
import re

from azure.mgmt.storage.models import StorageAccount

from cloudshell.cp.azure.common.operations_helper import OperationsHelper
from cloudshell.cp.azure.models.deploy_result_model import DeployResult


class DeployAzureVMOperation(object):
    def __init__(self,
                 logger,
                 vm_service,
                 network_service,
                 storage_service,
                 tags_service):
        """

        :param logger:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param tags_service:
        :return:
        """

        self.logger = logger
        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.tags_service = tags_service

    def deploy(self, azure_vm_deployment_model,
               cloud_provider_model,
               reservation,
               network_client,
               compute_client,
               storage_client,
               validator_factory):
        """
        :param cloudshell.cp.azure.common.validtors.validator_factory.ValidatorFactory validator_factory:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param reservation: cloudshell.cp.azure.models.reservation_model.ReservationModel
        :param cloudshell.cp.azure.models.deploy_azure_vm_resource_model.DeployAzureVMResourceModel azure_vm_deployment_model:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :return:
        """

        reservation_id = reservation.reservation_id

        app_name = azure_vm_deployment_model.app_name.lower().replace(" ", "")
        resource_name = app_name
        base_name = resource_name
        random_name = self._generate_name(base_name)
        group_name = str(reservation_id)
        interface_name = random_name
        ip_name = random_name
        computer_name = random_name
        admin_username = resource_name
        admin_password = 'ScJaw12deDFG'
        vm_name = random_name
        subnet_name = str(reservation_id)

        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(network_client=network_client,
                                                                                   group_name=cloud_provider_model.management_group_name,
                                                                                   tags_service=self.tags_service)

        subnet = next((subnet for subnet in sandbox_virtual_network.subnets if subnet.name == subnet_name), None)
        if subnet is None:
            raise Exception("Could not find a valid subnet.")

        storage_accounts_list = self.storage_service.get_storage_per_resource_group(storage_client, group_name)

        validator_factory.try_validate(resource_type=StorageAccount, resource=storage_accounts_list)

        storage_account_name = storage_accounts_list[0].name

        tags = self.tags_service.get_tags(vm_name, admin_username, subnet.name, reservation)

        try:
            # 1. Create network for vm
            nic = self.network_service.create_network_for_vm(network_client=network_client,
                                                             group_name=group_name,
                                                             interface_name=interface_name,
                                                             ip_name=ip_name,
                                                             region=cloud_provider_model.region,
                                                             subnet=subnet,
                                                             add_public_ip=azure_vm_deployment_model.add_public_ip,
                                                             public_ip_type=azure_vm_deployment_model.public_ip_type,
                                                             tags=tags)

            private_ip_address = nic.ip_configurations[0].private_ip_address

            # 2. create Vm
            result_create = self.vm_service.create_vm(compute_management_client=compute_client,
                                                      image_offer=azure_vm_deployment_model.image_offer,
                                                      image_publisher=azure_vm_deployment_model.image_publisher,
                                                      image_sku=azure_vm_deployment_model.image_sku,
                                                      image_version='latest',
                                                      admin_password=admin_password,
                                                      admin_username=admin_username,
                                                      computer_name=computer_name,
                                                      group_name=group_name,
                                                      nic_id=nic.id,
                                                      region=cloud_provider_model.region,
                                                      storage_name=storage_account_name,
                                                      vm_name=vm_name,
                                                      tags=tags,
                                                      instance_type=azure_vm_deployment_model.instance_type)

        except Exception as e:
            # On any exception removes all the created resources
            self.vm_service.delete_vm(compute_management_client=compute_client,
                                      group_name=group_name,
                                      vm_name=vm_name)

            self.network_service.delete_nic(network_client=network_client,
                                            group_name=group_name,
                                            interface_name=interface_name)

            self.network_service.delete_ip(network_client=network_client,
                                           group_name=group_name,
                                           ip_name=ip_name)

            raise e

        if azure_vm_deployment_model.add_public_ip:
            public_ip = self.network_service.get_public_ip(network_client=network_client,
                                                           group_name=group_name,
                                                           ip_name=ip_name)
            public_ip_address = public_ip.ip_address
        else:
            public_ip_address = None

        deployed_app_attributes = self._prepare_deployed_app_attributes(admin_username, admin_password,
                                                                        public_ip_address)

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
                            deployed_app_address=private_ip_address,
                            public_ip=public_ip_address,
                            resource_group=reservation_id)

    @staticmethod
    def validate_network(all_networks, group_name):
        if len(all_networks) > 1:
            raise Exception("The resource group {0} contains more than one virtual network.".format({group_name}))
        if len(all_networks) == 0:
            raise Exception("The resource group {0} does not contain a virtual network.".format({group_name}))

    @staticmethod
    def _generate_name(name, length=24):
        """Generate name based on the given one with a fixed length.

        Will replace all special characters (some Azure resources have this requirements).
        :param name:
        :param length:
        :return:
        """
        name = re.sub("[^a-zA-Z0-9]", "", name)
        generated_name = "{:.8}{}".format(uuid.uuid4().hex, name)

        return generated_name[:length]

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
