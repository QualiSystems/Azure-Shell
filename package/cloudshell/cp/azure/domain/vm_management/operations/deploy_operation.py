import uuid
import re

from azure.mgmt.storage.models import StorageAccount

from cloudshell.cp.azure.common.operations_helper import OperationsHelper
from cloudshell.cp.azure.models.deploy_result_model import DeployResult
from cloudshell.cp.azure.domain.services.parsers.rules_attribute_parser import RulesAttributeParser


class DeployAzureVMOperation(object):
    def __init__(self,
                 logger,
                 vm_service,
                 network_service,
                 storage_service,
                 tags_service,
                 security_group_service):
        """

        :param logger:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :return:
        """
        self.logger = logger
        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.tags_service = tags_service
        self.security_group_service = security_group_service

    def _process_nsg_rules(self, network_client, group_name, azure_vm_deployment_model, nic):
        """Create Network Security Group rules if needed

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param azure_vm_deployment_model: cloudshell.cp.azure.models.deploy_azure_vm_resource_model.DeployAzureVMResourceModel
        :param nic: azure.mgmt.network.models.NetworkInterface instance
        :return: None
        """
        network_security_groups = self.security_group_service.list_network_security_group(
            network_client=network_client,
            group_name=group_name)

        self._validate_resource(network_security_groups, group_name, "network security group")

        network_security_group = network_security_groups[0]

        if network_security_group.security_rules:
            last_rule = max(network_security_group.security_rules, key=lambda x: x.priority)
            last_priority = last_rule.priority
        else:
            last_priority = None

        inbound_rules = RulesAttributeParser.parse_port_group_attribute(
            ports_attribute=azure_vm_deployment_model.inbound_ports,
            last_priority=last_priority)

        if inbound_rules:
            self.security_group_service.create_network_security_group_rules(
                network_client=network_client,
                group_name=group_name,
                security_group_name=network_security_group.name,
                inbound_rules=inbound_rules,
                private_vm_ip=nic.ip_configurations[0].private_ip_address)

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

        all_networks = self.network_service.get_virtual_networks(network_client, group_name)

        self._validate_resource(all_networks, group_name, "virtual network")

        subnet = all_networks[0].subnets[0]

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

            self._process_nsg_rules(network_client=network_client,
                                    group_name=group_name,
                                    azure_vm_deployment_model=azure_vm_deployment_model,
                                    nic=nic)

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
                            deployed_app_address=public_ip_address,
                            public_ip=public_ip_address,
                            resource_group=reservation_id)

    def _validate_resource(self, resources_list, group_name, resource_name):
        if len(resources_list) > 1:
            raise Exception("The resource group {} contains more than one {}.".format(group_name, resource_name))
        if len(resources_list) == 0:
            raise Exception("The resource group {} does not contain a {}.".format(group_name, resource_name))

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
