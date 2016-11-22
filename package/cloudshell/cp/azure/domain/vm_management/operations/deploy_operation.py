import traceback

from azure.mgmt.storage.models import StorageAccount
from azure.mgmt.compute.models import OperatingSystemTypes

from cloudshell.cp.azure.common.operations_helper import OperationsHelper
from cloudshell.cp.azure.models.deploy_result_model import DeployResult
from cloudshell.cp.azure.domain.services.parsers.rules_attribute_parser import RulesAttributeParser


class DeployAzureVMOperation(object):
    CUSTOM_IMAGES_CONTAINER_PREFIX = "customimages"

    def __init__(self,
                 vm_service,
                 network_service,
                 storage_service,
                 vm_credentials_service,
                 key_pair_service,
                 tags_service,
                 security_group_service):
        """

        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.vm_credentials.VMCredentialsService vm_credentials_service:
        :param cloudshell.cp.azure.domain.services.key_pair.KeyPairService key_pair_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :return:
        """
        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.vm_credentials_service = vm_credentials_service
        self.key_pair_service = key_pair_service
        self.tags_service = tags_service
        self.security_group_service = security_group_service

    def _process_nsg_rules(self, network_client, group_name, azure_vm_deployment_model, nic):
        """Create Network Security Group rules if needed

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param azure_vm_deployment_model: deploy_azure_vm_resource_models.BaseDeployAzureVMResourceModel
        :param nic: azure.mgmt.network.models.NetworkInterface instance
        :return: None
        """

        if azure_vm_deployment_model.inbound_ports:
            inbound_rules = RulesAttributeParser.parse_port_group_attribute(
                ports_attribute=azure_vm_deployment_model.inbound_ports)

            network_security_group = self.security_group_service.get_network_security_group(
                network_client=network_client,
                group_name=group_name)

            self.security_group_service.create_network_security_group_rules(
                network_client=network_client,
                group_name=group_name,
                security_group_name=network_security_group.name,
                inbound_rules=inbound_rules,
                destination_addr=nic.ip_configurations[0].private_ip_address)

    def _get_sandbox_subnet(self, network_client, cloud_provider_model, subnet_name):
        """Get subnet for for given reservation

        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient
        :param cloud_provider_model: cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel
        :param subnet_name: (str) Azure subnet resource name
        :return: azure.mgmt.network.models.Subnet instance
        """
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(
            network_client=network_client,
            group_name=cloud_provider_model.management_group_name,
            tags_service=self.tags_service)

        try:
            return next(subnet for subnet in sandbox_virtual_network.subnets if subnet.name == subnet_name)
        except StopIteration:
            raise Exception("Could not find a valid subnet.")

    def _get_sandbox_storage_account_name(self, storage_client, group_name, validator_factory):
        """Get storage account name for given reservation

        :param storage_client: azure.mgmt.storage.storage_management_client.StorageManagementClient
        :param group_name:
        :param validator_factory:
        :return: (str) storage account name
        """
        storage_accounts_list = self.storage_service.get_storage_per_resource_group(storage_client, group_name)
        validator_factory.try_validate(resource_type=StorageAccount, resource=storage_accounts_list)

        return storage_accounts_list[0].name

    def _rollback_deployed_resources(self, compute_client, network_client, group_name, interface_name, vm_name, ip_name):
        """Remove all created resources by Deploy VM operation

        :param compute_client: azure.mgmt.compute.compute_management_client.ComputeManagementClient
        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param interface_name: Azure NIC resource name
        :param vm_name: Azure VM resource name
        :param ip_name: Azure Public IP address resource name
        :return:
        """
        self.vm_service.delete_vm(compute_management_client=compute_client,
                                  group_name=group_name,
                                  vm_name=vm_name)

        self.network_service.delete_nic(network_client=network_client,
                                        group_name=group_name,
                                        interface_name=interface_name)

        self.network_service.delete_ip(network_client=network_client,
                                       group_name=group_name,
                                       ip_name=ip_name)

    def _get_public_ip_address(self, network_client, azure_vm_deployment_model, group_name, ip_name):
        """Get Public IP address by Azure IP resource name

        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient instance
        :param azure_vm_deployment_model: deploy_azure_vm_resource_models.BaseDeployAzureVMResourceModel
        :param group_name: resource group name (reservation id)
        :param ip_name: Azure Public IP address resource name
        :return: (str) IP address or None
        """
        if azure_vm_deployment_model.add_public_ip:
            public_ip = self.network_service.get_public_ip(network_client=network_client,
                                                           group_name=group_name,
                                                           ip_name=ip_name)
            return public_ip.ip_address

    def deploy_from_custom_image(self, azure_vm_deployment_model, cloud_provider_model, reservation, network_client,
                                 compute_client, storage_client, validator_factory, logger):
        """Deploy Azure VM from custom image URN

        :param cloudshell.cp.azure.common.validtors.validator_factory.ValidatorFactory validator_factory:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param reservation: cloudshell.cp.azure.models.reservation_model.ReservationModel
        :param cloudshell.cp.azure.models.deploy_azure_vm_resource_models.DeployAzureVMFromCustomImageResourceModel azure_vm_deployment_model:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :param logging.Logger logger:
        :return:
        """
        reservation_id = reservation.reservation_id
        app_name = azure_vm_deployment_model.app_name.lower().replace(" ", "")
        resource_name = app_name
        base_name = resource_name
        random_name = OperationsHelper.generate_name(base_name)
        interface_name = random_name
        ip_name = random_name
        computer_name = random_name
        vm_name = random_name
        group_name = str(reservation_id)

        subnet = self._get_sandbox_subnet(network_client=network_client,
                                          cloud_provider_model=cloud_provider_model,
                                          subnet_name=group_name)

        storage_account_name = self._get_sandbox_storage_account_name(storage_client=storage_client,
                                                                      group_name=group_name,
                                                                      validator_factory=validator_factory)

        tags = self.tags_service.get_tags(vm_name, resource_name, subnet.name, reservation)

        blob_url_model = self.storage_service.parse_blob_url(azure_vm_deployment_model.image_urn)

        container_name_copy_to = "{}{}".format(self.CUSTOM_IMAGES_CONTAINER_PREFIX, blob_url_model.container_name)

        image_urn = self.storage_service.copy_blob(
            storage_client=storage_client,
            group_name_copy_to=group_name,
            storage_name_copy_to=storage_account_name,
            container_name_copy_to=container_name_copy_to,
            blob_name_copy_to=blob_url_model.blob_name,
            source_copy_from=azure_vm_deployment_model.image_urn,
            group_name_copy_from=cloud_provider_model.management_group_name)

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

            # 2. Prepare credentials for VM
            vm_credentials = self.vm_credentials_service.prepare_credentials(
                os_type=OperatingSystemTypes.windows,  # TODO: what OS type should be here? only Linux/Windows available
                username=azure_vm_deployment_model.username,
                password=azure_vm_deployment_model.password,
                storage_service=self.storage_service,
                key_pair_service=self.key_pair_service,
                storage_client=storage_client,
                group_name=group_name,
                storage_name=storage_account_name)

            # 3. create NSG rules
            self._process_nsg_rules(network_client=network_client,
                                    group_name=group_name,
                                    azure_vm_deployment_model=azure_vm_deployment_model,
                                    nic=nic)

            # 4. create Vm
            result_create = self.vm_service.create_vm_from_custom_image(
                compute_management_client=compute_client,
                image_urn=image_urn,
                image_os_type=azure_vm_deployment_model.image_os_type,
                vm_credentials=vm_credentials,
                computer_name=computer_name,
                group_name=group_name,
                nic_id=nic.id,
                region=cloud_provider_model.region,
                storage_name=storage_account_name,
                vm_name=vm_name,
                tags=tags,
                instance_type=azure_vm_deployment_model.instance_type)

        except Exception:
            self._rollback_deployed_resources(compute_client=compute_client,
                                              network_client=network_client,
                                              group_name=group_name,
                                              interface_name=interface_name,
                                              vm_name=vm_name,
                                              ip_name=ip_name)

            logger.error("Failed to deploy VM From custom Image. Error: {0}".format(traceback.format_exc()))
            raise

        public_ip_address = self._get_public_ip_address(network_client=network_client,
                                                        azure_vm_deployment_model=azure_vm_deployment_model,
                                                        group_name=group_name,
                                                        ip_name=ip_name)

        deployed_app_attributes = self._prepare_deployed_app_attributes(
            vm_credentials.admin_username,
            vm_credentials.admin_password,
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

    def deploy(self, azure_vm_deployment_model,
               cloud_provider_model,
               reservation,
               network_client,
               compute_client,
               storage_client,
               validator_factory,
               logger):
        """
        :param cloudshell.cp.azure.common.validtors.validator_factory.ValidatorFactory validator_factory:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param reservation: cloudshell.cp.azure.models.reservation_model.ReservationModel
        :param cloudshell.cp.azure.models.deploy_azure_vm_resource_models.DeployAzureVMResourceModel azure_vm_deployment_model:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :param logging.Logger logger:
        :return:
        """

        reservation_id = reservation.reservation_id
        app_name = azure_vm_deployment_model.app_name.replace(" ", "")
        resource_name = app_name
        base_name = resource_name
        random_name = OperationsHelper.generate_name(base_name)
        group_name = str(reservation_id)
        interface_name = random_name
        ip_name = random_name
        computer_name = random_name
        vm_name = random_name

        subnet = self._get_sandbox_subnet(network_client=network_client,
                                          cloud_provider_model=cloud_provider_model,
                                          subnet_name=group_name)

        storage_account_name = self._get_sandbox_storage_account_name(storage_client=storage_client,
                                                                      group_name=group_name,
                                                                      validator_factory=validator_factory)

        tags = self.tags_service.get_tags(vm_name, resource_name, subnet.name, reservation)

        os_type = self.vm_service.get_image_operation_system(
            compute_management_client=compute_client,
            location=cloud_provider_model.region,
            publisher_name=azure_vm_deployment_model.image_publisher,
            offer=azure_vm_deployment_model.image_offer,
            skus=azure_vm_deployment_model.image_sku)

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

            # 2. Prepare credentials for VM
            vm_credentials = self.vm_credentials_service.prepare_credentials(
                os_type=os_type,
                username=azure_vm_deployment_model.username,
                password=azure_vm_deployment_model.password,
                storage_service=self.storage_service,
                key_pair_service=self.key_pair_service,
                storage_client=storage_client,
                group_name=group_name,
                storage_name=storage_account_name)

            # 3. create NSG rules
            self._process_nsg_rules(network_client=network_client,
                                    group_name=group_name,
                                    azure_vm_deployment_model=azure_vm_deployment_model,
                                    nic=nic)

            # 4. create Vm
            result_create = self.vm_service.create_vm(compute_management_client=compute_client,
                                                      image_offer=azure_vm_deployment_model.image_offer,
                                                      image_publisher=azure_vm_deployment_model.image_publisher,
                                                      image_sku=azure_vm_deployment_model.image_sku,
                                                      image_version='latest',
                                                      vm_credentials=vm_credentials,
                                                      computer_name=computer_name,
                                                      group_name=group_name,
                                                      nic_id=nic.id,
                                                      region=cloud_provider_model.region,
                                                      storage_name=storage_account_name,
                                                      vm_name=vm_name,
                                                      tags=tags,
                                                      instance_type=azure_vm_deployment_model.instance_type)

        except Exception:
            self._rollback_deployed_resources(compute_client=compute_client,
                                              network_client=network_client,
                                              group_name=group_name,
                                              interface_name=interface_name,
                                              vm_name=vm_name,
                                              ip_name=ip_name)

            logger.error("Failed to deploy VM. Error: {0}".format(traceback.format_exc()))
            raise

        public_ip_address = self._get_public_ip_address(network_client=network_client,
                                                        azure_vm_deployment_model=azure_vm_deployment_model,
                                                        group_name=group_name,
                                                        ip_name=ip_name)

        deployed_app_attributes = self._prepare_deployed_app_attributes(
            vm_credentials.admin_username,
            vm_credentials.admin_password,
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


    def _validate_resource_is_single_per_group(self, resources_list, group_name, resource_name):
        if len(resources_list) > 1:
            raise Exception("The resource group {} contains more than one {}.".format(group_name, resource_name))
        if len(resources_list) == 0:
            raise Exception("The resource group {} does not contain a {}.".format(group_name, resource_name))

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
