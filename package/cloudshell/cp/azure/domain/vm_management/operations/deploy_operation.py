import re

from cloudshell.cp.azure.domain.common.vm_details_provider import VmDetailsProvider
from msrestazure.azure_exceptions import CloudError
from cloudshell.cp.azure.common.exceptions.quali_timeout_exception import QualiTimeoutException, \
    QualiScriptExecutionTimeoutException
from cloudshell.cp.azure.models.deploy_result_model import DeployResult
from cloudshell.cp.azure.common.parsers.rules_attribute_parser import RulesAttributeParser
from cloudshell.cp.azure.models.reservation_model import ReservationModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import \
    DeployAzureVMFromCustomImageResourceModel, BaseDeployAzureVMResourceModel, DeployAzureVMResourceModel
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from azure.mgmt.network.models import Subnet, NetworkInterface
from azure.mgmt.compute.models import OperatingSystemTypes, PurchasePlan
from cloudshell.shell.core.driver_context import CancellationContext
from cloudshell.cp.azure.models.vm_credentials import VMCredentials
from cloudshell.cp.azure.models.image_data import ImageDataModelBase, MarketplaceImageDataModel
from cloudshell.api.cloudshell_api import CloudShellAPISession


class DeployAzureVMOperation(object):
    CUSTOM_IMAGES_CONTAINER_PREFIX = "customimages-"

    def __init__(self,
                 vm_service,
                 network_service,
                 storage_service,
                 vm_credentials_service,
                 key_pair_service,
                 tags_service,
                 security_group_service,
                 name_provider_service,
                 vm_extension_service,
                 cancellation_service,
                 generic_lock_provider,
                 image_data_factory,
                 vm_details_provider):
        """

        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.vm_credentials.VMCredentialsService vm_credentials_service:
        :param cloudshell.cp.azure.domain.services.key_pair.KeyPairService key_pair_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :param cloudshell.cp.azure.domain.services.name_provider.NameProviderService name_provider_service:
        :param cloudshell.cp.azure.domain.services.vm_extension.VMExtensionService vm_extension_service:
        :param cloudshell.cp.azure.domain.services.command_cancellation.CommandCancellationService cancellation_service:
        :param cloudshell.cp.azure.domain.services.lock_service.GenericLockProvider generic_lock_provider:
        :param cloudshell.cp.azure.domain.services.image_data.ImageDataFactory image_data_factory:
        :param cloudshell.cp.azure.domain.common.vm_details_provider.VmDetailsProvider vm_details_provider:
        :return:
        """

        self.image_data_factory = image_data_factory
        self.generic_lock_provider = generic_lock_provider
        self.vm_service = vm_service
        self.network_service = network_service
        self.storage_service = storage_service
        self.vm_credentials_service = vm_credentials_service
        self.key_pair_service = key_pair_service
        self.tags_service = tags_service
        self.security_group_service = security_group_service
        self.name_provider_service = name_provider_service
        self.vm_extension_service = vm_extension_service
        self.cancellation_service = cancellation_service
        self.vm_details_provider = vm_details_provider

    def deploy_from_custom_image(self, deployment_model,
                                 cloud_provider_model,
                                 reservation,
                                 network_client,
                                 compute_client,
                                 storage_client,
                                 cancellation_context,
                                 logger,
                                 cloudshell_session):
        """ Deploy Azure VM from custom image URN

        :param CloudShellAPISession cloudshell_session:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param ReservationModel reservation:
        :param DeployAzureVMFromCustomImageResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param logging.Logger logger:
        :param CancellationContext cancellation_context:
        :return:
        """
        logger.info("Start Deploy Azure VM From Custom Image operation")

        return self._deploy_vm_generic(create_vm_action=self._create_vm_custom_image_action,
                                       deployment_model=deployment_model,
                                       cloud_provider_model=cloud_provider_model,
                                       reservation=reservation,
                                       storage_client=storage_client,
                                       compute_client=compute_client,
                                       network_client=network_client,
                                       cancellation_context=cancellation_context,
                                       logger=logger,
                                       cloudshell_session=cloudshell_session)

    def deploy_from_marketplace(self, deployment_model,
                                cloud_provider_model,
                                reservation,
                                network_client,
                                compute_client,
                                storage_client,
                                cancellation_context,
                                logger,
                                cloudshell_session):
        """
        :param CloudShellAPISession cloudshell_session:
        :param CancellationContext cancellation_context:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param reservation: cloudshell.cp.azure.models.reservation_model.ReservationModel
        :param cloudshell.cp.azure.models.deploy_azure_vm_resource_models.DeployAzureVMResourceModel deployment_model:
        :param cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel cloud_provider_model:cloud provider
        :param logging.Logger logger:
        :return:
        """
        logger.info("Start Deploy Azure VM from marketplace operation")

        return self._deploy_vm_generic(create_vm_action=self._create_vm_marketplace_action,
                                       deployment_model=deployment_model,
                                       cloud_provider_model=cloud_provider_model,
                                       reservation=reservation,
                                       storage_client=storage_client,
                                       compute_client=compute_client,
                                       network_client=network_client,
                                       cancellation_context=cancellation_context,
                                       logger=logger,
                                       cloudshell_session=cloudshell_session)

    def _deploy_vm_generic(self, create_vm_action, deployment_model, cloud_provider_model, reservation, storage_client,
                           compute_client, network_client, cancellation_context, logger, cloudshell_session):
        """

        :param create_vm_action: action that returns a VM object with the following signature:
            (compute_client, storage_client, deployment_model, cloud_provider_model, data, cancellation_context, logger)
        :param BaseDeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param azure.mgmt.compute.compu;te_management_client.ComputeManagementClient compute_client:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param CancellationContext cancellation_context:
        :param logging.Logger logger:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session:
        :return:
        """
        logger.info("Start Deploy Azure VM operation")
        extension_time_out = False

        # 1. prepare deploy data model object
        data = self._prepare_deploy_data(logger=logger,
                                         reservation=reservation,
                                         deployment_model=deployment_model,
                                         cloud_provider_model=cloud_provider_model,
                                         network_client=network_client,
                                         storage_client=storage_client,
                                         compute_client=compute_client)

        self.cancellation_service.check_if_cancelled(cancellation_context)

        try:
            # 2. create NIC + Credentials & update NSG
            data = self._create_vm_common_objects(
                    logger=logger,
                    data=data,
                    deployment_model=deployment_model,
                    cloud_provider_model=cloud_provider_model,
                    network_client=network_client,
                    storage_client=storage_client,
                    cancellation_context=cancellation_context)

            # 3. create VM
            logger.info("Start Deploying VM {}".format(data.vm_name))

            try:
                vm = create_vm_action(deployment_model=deployment_model,
                                      cloud_provider_model=cloud_provider_model,
                                      data=data,
                                      compute_client=compute_client,
                                      cancellation_context=cancellation_context,
                                      logger=logger)
            except CloudError as exc:
                self._expand_cloud_error_message(exc, deployment_model)
                raise

            logger.info("VM {} was successfully deployed".format(data.vm_name))

            self.cancellation_service.check_if_cancelled(cancellation_context)

            # 4. create custom script extension
            self._create_vm_custom_script_extension(
                    deployment_model=deployment_model,
                    cloud_provider_model=cloud_provider_model,
                    compute_client=compute_client,
                    data=data,
                    logger=logger,
                    cancellation_context=cancellation_context)

        except QualiScriptExecutionTimeoutException, e:
            logger.info(e.message)
            html_format = "<html><body><span style='color: red;'>{0}</span></body></html>".format(e.message)
            cloudshell_session.WriteMessageToReservationOutput(reservationId=reservation.reservation_id,
                                                               message=html_format)
            extension_time_out = True

        except Exception:
            logger.exception("Failed to deploy VM from marketplace. Error:")
            self._rollback_deployed_resources(compute_client=compute_client,
                                              network_client=network_client,
                                              group_name=data.group_name,
                                              interface_name=data.interface_name,
                                              vm_name=data.vm_name,
                                              ip_name=data.ip_name,
                                              logger=logger)
            raise

        logger.info("VM {} was successfully deployed".format(data.vm_name))

        data.public_ip_address = self._get_public_ip_address(network_client=network_client,
                                                             azure_vm_deployment_model=deployment_model,
                                                             group_name=data.group_name,
                                                             ip_name=data.ip_name,
                                                             cancellation_context=cancellation_context,
                                                             logger=logger)

        deployed_app_attributes = self._prepare_deployed_app_attributes(
                admin_username=data.vm_credentials.admin_username,
                admin_password=data.vm_credentials.admin_password,
                public_ip=data.public_ip_address)

        # check if CustomImageDataModel or MarketplaceImageDataModel, no more options
        is_market_place = type(data.image_model) is MarketplaceImageDataModel
        vm_details_data = self.vm_details_provider.create(vm, is_market_place, logger, network_client, data.group_name)

        return DeployResult(vm_name=data.vm_name,
                            vm_uuid=vm.vm_id,
                            cloud_provider_resource_name=cloud_provider_model.cloud_provider_name,
                            autoload=deployment_model.autoload,
                            inbound_ports=deployment_model.inbound_ports,
                            deployed_app_attributes=deployed_app_attributes,
                            deployed_app_address=data.private_ip_address,
                            public_ip=data.public_ip_address,
                            resource_group=data.reservation_id,
                            extension_time_out=extension_time_out,
                            vm_details_data=vm_details_data)

    def _expand_cloud_error_message(self, exc, deployment_model):
        """
        :param CloudError exc:
        :param BaseDeployAzureVMResourceModel deployment_model:
        :return:
        """
        match = re.search('storage account type .+ is not supported for vm size', exc.message.lower())
        if match:
            exc.error.message += "\nDisk Type attribute value {} doesn't support the selected VM size.".format(
                deployment_model.disk_type)

    def _create_vm_custom_image_action(self, compute_client, deployment_model, cloud_provider_model,
                                       data, cancellation_context, logger):
        """
        :param DeployAzureVMFromCustomImageResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param DeployAzureVMOperation.DeployDataModel data:
        :param CancellationContext cancellation_context:
        :param logging.Logger logger:
        :return:
        :rtype: azure.mgmt.compute.models.VirtualMachine
        """

        self.cancellation_service.check_if_cancelled(cancellation_context)

        # create VM
        logger.info("Start creating VM {} From custom image {} from resource group {}"
                    .format(data.vm_name, deployment_model.image_name, deployment_model.image_resource_group))

        return self.vm_service.create_vm_from_custom_image(
                compute_management_client=compute_client,
                image_name=deployment_model.image_name,
                image_resource_group=deployment_model.image_resource_group,
                disk_type=deployment_model.disk_type,
                vm_credentials=data.vm_credentials,
                computer_name=data.computer_name,
                group_name=data.group_name,
                nic_id=data.nic.id,
                region=cloud_provider_model.region,
                vm_name=data.vm_name,
                tags=data.tags,
                vm_size=data.vm_size,
                cancellation_context=cancellation_context)

    def _create_vm_marketplace_action(self, compute_client, deployment_model, cloud_provider_model,
                                      data, cancellation_context, logger):
        """
        :param DeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param DeployAzureVMOperation.DeployDataModel data:
        :param CancellationContext cancellation_context:
        :param logging.Logger logger:
        :return:
        :rtype: azure.mgmt.compute.models.VirtualMachine
        """
        return self.vm_service.create_vm_from_marketplace(
                compute_management_client=compute_client,
                image_offer=deployment_model.image_offer,
                image_publisher=deployment_model.image_publisher,
                image_sku=deployment_model.image_sku,
                image_version=deployment_model.image_version,
                disk_type=deployment_model.disk_type,
                vm_credentials=data.vm_credentials,
                computer_name=data.computer_name,
                group_name=data.group_name,
                nic_id=data.nic.id,
                region=cloud_provider_model.region,
                vm_name=data.vm_name,
                tags=data.tags,
                vm_size=data.vm_size,
                purchase_plan=data.image_model.purchase_plan,  # type should be MarketplaceImageDataModel
                cancellation_context=cancellation_context)

    def _process_nsg_rules(self, network_client, group_name, azure_vm_deployment_model, nic,
                           cancellation_context, logger):
        """
        Create Network Security Group rules if needed

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param azure_vm_deployment_model: deploy_azure_vm_resource_models.BaseDeployAzureVMResourceModel
        :param nic: azure.mgmt.network.models.NetworkInterface instance
        :param logger: logging.Logger instance
        :return: None
        """
        logger.info("Process inbound rules: {}".format(azure_vm_deployment_model.inbound_ports))

        if azure_vm_deployment_model.inbound_ports:
            inbound_rules = RulesAttributeParser.parse_port_group_attribute(
                    ports_attribute=azure_vm_deployment_model.inbound_ports)

            logger.info("Parsed inbound rules {}".format(inbound_rules))

            logger.info("Get NSG by group name {}".format(group_name))
            network_security_group = self.security_group_service.get_network_security_group(
                    network_client=network_client,
                    group_name=group_name)

            self.cancellation_service.check_if_cancelled(cancellation_context)

            logger.info("Create rules for the NSG {}".format(network_security_group.name))
            lock = self.generic_lock_provider.get_resource_lock(lock_key=group_name, logger=logger)
            self.security_group_service.create_network_security_group_rules(
                    network_client=network_client,
                    group_name=group_name,
                    security_group_name=network_security_group.name,
                    inbound_rules=inbound_rules,
                    destination_addr=nic.ip_configurations[0].private_ip_address,
                    lock=lock)

            logger.info("NSG rules were successfully created for NSG {}".format(network_security_group.name))
            self.cancellation_service.check_if_cancelled(cancellation_context)

    def _get_sandbox_subnet(self, network_client, cloud_provider_model, subnet_name, logger):
        """
        Get subnet for for given reservation

        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient
        :param cloud_provider_model: cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel
        :param subnet_name: (str) Azure subnet resource name
        :param logger: logging.Logger instance
        :return: azure.mgmt.network.models.Subnet instance
        """
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(
                network_client=network_client,
                group_name=cloud_provider_model.management_group_name)

        try:
            return next(subnet for subnet in sandbox_virtual_network.subnets if subnet.name == subnet_name)
        except StopIteration:
            logger.error("Subnet {} was not found under the resource group {}".format(
                    subnet_name, cloud_provider_model.management_group_name))
            raise Exception("Could not find a valid subnet.")

    def _rollback_deployed_resources(self, compute_client, network_client, group_name, interface_name, vm_name,
                                     ip_name, logger):
        """
        Remove all created resources by Deploy VM operation on any Exception.
        This method doesnt support cancellation because full cleanup is mandatory for successful deletion of subnet
        during cleanup-connectivity.

        :param compute_client: azure.mgmt.compute.compute_management_client.ComputeManagementClient
        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param interface_name: Azure NIC resource name
        :param vm_name: Azure VM resource name
        :param ip_name: Azure Public IP address resource name
        :param logger: logging.Logger instance
        :return:
        """
        logger.info("Delete VM {} ".format(vm_name))
        self.vm_service.delete_vm(compute_management_client=compute_client,
                                  group_name=group_name,
                                  vm_name=vm_name)

        logger.info("Delete NIC {} ".format(interface_name))
        self.network_service.delete_nic(network_client=network_client,
                                        group_name=group_name,
                                        interface_name=interface_name)

        logger.info("Delete IP {} ".format(ip_name))
        self.network_service.delete_ip(network_client=network_client,
                                       group_name=group_name,
                                       ip_name=ip_name)

    def _get_public_ip_address(self, network_client, azure_vm_deployment_model, group_name, ip_name,
                               cancellation_context, logger):
        """
        Get Public IP address by Azure IP resource name

        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient instance
        :param azure_vm_deployment_model: deploy_azure_vm_resource_models.BaseDeployAzureVMResourceModel
        :param group_name: resource group name (reservation id)
        :param ip_name: Azure Public IP address resource name
        :param logger: logging.Logger instance
        :return: (str) IP address or None
        """
        if azure_vm_deployment_model.add_public_ip:
            logger.info("Retrieve Public IP {}".format(ip_name))
            public_ip = self.network_service.get_public_ip(network_client=network_client,
                                                           group_name=group_name,
                                                           ip_name=ip_name)
            ip_address = public_ip.ip_address
            logger.info("Public IP is {}".format(ip_address))

            self.cancellation_service.check_if_cancelled(cancellation_context)

            return ip_address

    def _prepare_computer_name(self, name, postfix, os_type):
        """
        Prepare computer name for the VM

        :param str name: app_name name
        :param str postfix: postfix to add to the app name
        :param OperatingSystemTypes os_type: The os type dictated the lenght of the computer name. Max length for windows is 15.
        Max length for linux is 64.
        :return: computer name
        """
        # max length for the Windows computer name must 15
        length = 15 if os_type == OperatingSystemTypes.windows else 64
        return self.name_provider_service.generate_name(name=name, postfix=postfix, max_length=length)

    def _prepare_vm_size(self, azure_vm_deployment_model, cloud_provider_model):
        """
        Prepare Azure VM Size

        :param BaseDeployAzureVMResourceModel azure_vm_deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :return: (str) Azure VM Size
        """
        vm_size = azure_vm_deployment_model.vm_size or cloud_provider_model.vm_size

        if not vm_size:
            raise Exception('There is no value for "VM Size" attribute neither on the '
                            'Deployment model nor on the Cloud Provider one')

        return vm_size

    def _create_vm_custom_script_extension(self, deployment_model, cloud_provider_model, compute_client, data,
                                           logger, cancellation_context):
        """ Create VM custom script extension if data exist in deployment model

        :param BaseDeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param DeployAzureVMOperation.DeployDataModel data:
        :param logging.Logger logger:
        :param CancellationContext cancellation_context:
        :return:
        """

        # Create VM Extension
        if not deployment_model.extension_script_file:
            logger.info("No VM Custom Script Extension for VM {}".format(data.vm_name))
            return

        self.cancellation_service.check_if_cancelled(cancellation_context)

        logger.info("Processing VM Custom Script Extension for VM {}".format(data.vm_name))

        try:
            self.vm_extension_service.create_script_extension(
                    compute_client=compute_client,
                    location=cloud_provider_model.region,
                    group_name=data.group_name,
                    vm_name=data.vm_name,
                    image_os_type=data.image_model.os_type,
                    script_file=deployment_model.extension_script_file,
                    script_configurations=deployment_model.extension_script_configurations,
                    tags=data.tags,
                    cancellation_context=cancellation_context,
                    timeout=deployment_model.extension_script_timeout)

            logger.info("VM Custom Script Extension for VM {} was successfully deployed".format(data.vm_name))
        except QualiTimeoutException:
            seconds = deployment_model.extension_script_timeout

            msg = "App {0} was partially deployed - " \
                  "Custom script extension reached maximum timeout of {1} minutes and {2} seconds" \
                .format(deployment_model.app_name, seconds / 60, seconds % 60)
            raise QualiScriptExecutionTimeoutException(msg)
        except Exception:
            raise

        self.cancellation_service.check_if_cancelled(cancellation_context)

    def _create_vm_common_objects(self, logger, data, deployment_model, cloud_provider_model, network_client,
                                  storage_client, cancellation_context):
        """ Creates and configures common VM objects: NIC, Credentials, NSG (if needed)

        :param DeployAzureVMOperation.DeployDataModel data:
        :param BaseDeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param logging.Logger logger:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param azure.mgmt.network.network_management_client.StorageManagementClient storage_client:
        :param CancellationContext cancellation_context:
        :return: Updated DeployDataModel instance
        :rtype: DeployAzureVMOperation.DeployDataModel
        """
        # 1. Create network for vm
        logger.info("Creating NIC '{}'".format(data.interface_name))
        data.nic = self.network_service.create_network_for_vm(network_client=network_client,
                                                              group_name=data.group_name,
                                                              interface_name=data.interface_name,
                                                              ip_name=data.ip_name,
                                                              cloud_provider_model=cloud_provider_model,
                                                              subnet=data.subnet,
                                                              add_public_ip=deployment_model.add_public_ip,
                                                              public_ip_type=deployment_model.public_ip_type,
                                                              tags=data.tags,
                                                              logger=logger)

        data.private_ip_address = data.nic.ip_configurations[0].private_ip_address
        logger.info("NIC private IP is {}".format(data.private_ip_address))

        self.cancellation_service.check_if_cancelled(cancellation_context)

        # 2. create NSG rules
        logger.info("Processing Network Security Group rules")
        self._process_nsg_rules(network_client=network_client,
                                group_name=data.group_name,
                                azure_vm_deployment_model=deployment_model,
                                nic=data.nic,
                                cancellation_context=cancellation_context,
                                logger=logger)

        self.cancellation_service.check_if_cancelled(cancellation_context)

        # 3. Prepare credentials for VM
        logger.info("Prepare credentials for the VM {}".format(data.vm_name))
        data.vm_credentials = self.vm_credentials_service.prepare_credentials(
                os_type=data.image_model.os_type,
                username=deployment_model.username,
                password=deployment_model.password,
                storage_service=self.storage_service,
                key_pair_service=self.key_pair_service,
                storage_client=storage_client,
                group_name=data.group_name,
                storage_name=data.storage_account_name)

        self.cancellation_service.check_if_cancelled(cancellation_context)

        return data

    def _validate_deployment_model(self, vm_deployment_model, os_type):
        """
        :param BaseDeployAzureVMResourceModel vm_deployment_model:
        :param OperatingSystemTypes image_os_type: (enum) windows/linux value os_type
        """
        if vm_deployment_model.inbound_ports and not vm_deployment_model.add_public_ip:
            raise Exception('"Inbound Ports" attribute must be empty when "Add Public IP" is false')

        if vm_deployment_model.extension_script_file:
            self.vm_extension_service.validate_script_extension(
                    image_os_type=os_type,
                    script_file=vm_deployment_model.extension_script_file,
                    script_configurations=vm_deployment_model.extension_script_configurations)

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

    def _prepare_deploy_data(self, logger, reservation, deployment_model, cloud_provider_model,
                             network_client, storage_client, compute_client):
        """
        :param logging.Logger logger:
        :param ReservationModel reservation:
        :param BaseDeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model: cloud provider
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param azure.mgmt.storage.storage_management_client.ComputeManagementClient compute_client:
        :return:
        :rtype: DeployAzureVMOperation.DeployDataModel
        """

        image_data_model = self.image_data_factory.get_image_data_model(
                cloud_provider_model=cloud_provider_model,
                deployment_model=deployment_model,
                compute_client=compute_client,
                logger=logger)

        self._validate_deployment_model(vm_deployment_model=deployment_model, os_type=image_data_model.os_type)

        data = self.DeployDataModel()

        data.reservation_id = str(reservation.reservation_id)
        data.group_name = str(reservation.reservation_id)
        data.image_model = image_data_model

        # normalize the app name to a valid Azure vm name
        data.app_name = self.name_provider_service.normalize_name(deployment_model.app_name)

        resource_postfix = self.name_provider_service.generate_short_unique_string()
        unique_resource_name = self.name_provider_service.generate_name(name=data.app_name,
                                                                        postfix=resource_postfix,
                                                                        max_length=64)
        data.interface_name = unique_resource_name
        data.ip_name = unique_resource_name
        data.vm_name = unique_resource_name
        data.computer_name = self._prepare_computer_name(name=data.app_name,
                                                         postfix=resource_postfix,
                                                         os_type=data.image_model.os_type)

        data.vm_size = self._prepare_vm_size(azure_vm_deployment_model=deployment_model,
                                             cloud_provider_model=cloud_provider_model)

        logger.info("Retrieve sandbox subnet {}".format(data.group_name))
        data.subnet = self._get_sandbox_subnet(network_client=network_client,
                                               cloud_provider_model=cloud_provider_model,
                                               subnet_name=data.group_name,
                                               logger=logger)

        logger.info("Retrieve sandbox storage account name by resource group {}".format(data.group_name))
        data.storage_account_name = self.storage_service.get_sandbox_storage_account_name(storage_client=storage_client,
                                                                                          group_name=data.group_name)

        data.tags = self.tags_service.get_tags(vm_name=data.vm_name, reservation=reservation)
        logger.info("Tags for the VM {}".format(data.tags))

        return data

    class DeployDataModel(object):
        def __init__(self):
            self.reservation_id = ''  # type: str
            self.app_name = ''  # type: str
            self.group_name = ''  # type: str
            self.interface_name = ''  # type: str
            self.ip_name = ''  # type: str
            self.computer_name = ''  # type: str
            self.vm_name = ''  # type: str
            self.vm_size = ''  # type: str
            self.subnet = None  # type: Subnet
            self.storage_account_name = ''  # type: str
            self.tags = {}  # type: dict
            self.image_model = None  # type: ImageDataModelBase
            self.os_type = ''  # type: OperatingSystemTypes
            self.nic = None  # type: NetworkInterface
            self.vm_credentials = None  # type: VMCredentials
            self.private_ip_address = ''  # type: str
            self.public_ip_address = ''  # type: str
