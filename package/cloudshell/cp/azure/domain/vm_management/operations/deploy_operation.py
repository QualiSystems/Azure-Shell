import uuid
import re

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
               storage_client,
               network_client,
               compute_client,
               resource_client):
        """
        :param storage_client:
        :param resource_client:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param network_client:
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
        network_name = base_name
        subnet_name = base_name
        ip_name = random_name
        storage_account_name = random_name
        computer_name = random_name
        admin_username = resource_name
        admin_password = 'ScJaw12deDFG'
        vm_name = random_name
        tags = self.tags_service.get_tags(vm_name, admin_username, subnet_name, reservation)

        try:
            # 1. Crate a resource group
            self.vm_service.create_resource_group(resource_management_client=resource_client,
                                                  group_name=group_name,
                                                  region=cloud_provider_model.region,
                                                  tags=tags)

            # 2. Create a storage account
            self.storage_service.create_storage_account(storage_client=storage_client,
                                                        group_name=group_name,
                                                        region=cloud_provider_model.region,
                                                        storage_account_name=storage_account_name,
                                                        tags=tags)

            # 3. Create the network interface
            nic = self.network_service.create_network(network_client=network_client,
                                                      group_name=group_name,
                                                      interface_name=interface_name,
                                                      ip_name=ip_name,
                                                      network_name=network_name,
                                                      region=cloud_provider_model.region,
                                                      subnet_name=subnet_name,
                                                      add_public_ip=azure_vm_deployment_model.add_public_ip,
                                                      public_ip_type=azure_vm_deployment_model.public_ip_type,
                                                      tags=tags)

            # 4. create Vm
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

            self.network_service.delete_nic(network_client=network_client,
                                            group_name=group_name,
                                            interface_name=interface_name)

            self.network_service.delete_ip(network_client=network_client,
                                           group_name=group_name,
                                           ip_name=ip_name)

            self.vm_service.delete_vm(compute_management_client=compute_client,
                                      group_name=group_name,
                                      vm_name=vm_name)

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
                            deployed_app_address=nic.ip_configurations[0].private_ip_address,
                            public_ip=public_ip_address,
                            resource_group=reservation_id)

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
