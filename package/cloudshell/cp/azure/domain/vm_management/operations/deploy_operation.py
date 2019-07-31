import re

from azure.mgmt.compute.models import OperatingSystemTypes
from azure.mgmt.network.models import SecurityRuleAccess
from azure.mgmt.network.models import SecurityRuleProtocol
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.cp.core.models import DeployAppResult, Attribute, ConnectSubnet
from cloudshell.shell.core.driver_context import CancellationContext
from msrestazure.azure_exceptions import CloudError

from cloudshell.cp.azure.common.exceptions.quali_timeout_exception import QualiTimeoutException, \
    QualiScriptExecutionTimeoutException
from cloudshell.cp.azure.common.helpers.ip_allocation_helper import is_static_allocation
from cloudshell.cp.azure.common.parsers.rules_attribute_parser import RulesAttributeParser
from cloudshell.cp.azure.domain.services.network_service import NetworkService
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import \
    DeployAzureVMFromCustomImageResourceModel, BaseDeployAzureVMResourceModel, DeployAzureVMResourceModel
from cloudshell.cp.azure.models.image_data import MarketplaceImageDataModel
from cloudshell.cp.azure.models.nic_request import NicRequest
from cloudshell.cp.azure.models.reservation_model import ReservationModel
from cloudshell.cp.azure.models.rule_data import RuleData


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
                 vm_details_provider,
                 ip_service):
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
        :param cloudshell.cp.azure.domain.services.ip_service.IpService ip_service:
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
        self.ip_service = ip_service

    def deploy_from_custom_image(self, deployment_model,
                                 cloud_provider_model,
                                 reservation,
                                 network_client,
                                 compute_client,
                                 storage_client,
                                 cancellation_context,
                                 logger,
                                 cloudshell_session,
                                 network_actions):
        """ Deploy Azure VM from custom image URN
        :param list[ConnectSubnet] network_actions:
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
                                       deployment_model=deployment_model, cloud_provider_model=cloud_provider_model,
                                       reservation=reservation, storage_client=storage_client,
                                       compute_client=compute_client, network_client=network_client,
                                       cancellation_context=cancellation_context, logger=logger,
                                       cloudshell_session=cloudshell_session, network_actions=network_actions)

    def deploy_from_marketplace(self, deployment_model, cloud_provider_model, reservation, network_client,
                                compute_client, storage_client, cancellation_context, logger, cloudshell_session,
                                network_actions):
        """
        :param list[ConnectSubnet] network_actions:
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
                                       network_actions=network_actions,
                                       cancellation_context=cancellation_context,
                                       logger=logger,
                                       cloudshell_session=cloudshell_session)

    def _deploy_vm_generic(self, create_vm_action, deployment_model, cloud_provider_model, reservation, storage_client,
                           compute_client, network_client, cancellation_context, logger, cloudshell_session,
                           network_actions):
        """

        :param list[ConnectSubnet] network_actions:
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
        :return: cloudshell.cp.core.models.DeployAppResult
        """
        logger.info("Start Deploy Azure VM operation")

        # 1. prepare deploy data model object
        data = self._prepare_deploy_data(logger=logger,
                                         reservation=reservation,
                                         deployment_model=deployment_model,
                                         cloud_provider_model=cloud_provider_model,
                                         network_client=network_client,
                                         storage_client=storage_client,
                                         compute_client=compute_client,
                                         network_actions=network_actions)

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
                cancellation_context=cancellation_context,
                cloudshell_session=cloudshell_session)

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
            # todo alexa - release ip from pool if needed
            self._rollback_deployed_resources(compute_client=compute_client,
                                              network_client=network_client,
                                              group_name=data.group_name,
                                              nic_requests=data.nic_requests,
                                              vm_name=data.vm_name,
                                              logger=logger,
                                              private_ip_allocation_method=cloud_provider_model.private_ip_allocation_method,
                                              allocated_private_ips=data.all_private_ip_addresses,
                                              reservation_id=data.reservation_id,
                                              cloudshell_session=cloudshell_session)
            raise

        logger.info("VM {} was successfully deployed".format(data.vm_name))

        if data.nic_requests and any(n.is_public for n in data.nic_requests):
            # the name of the first interface we requested to be connected to a public subnet
            request_to_connect_to_public_subnet = next(n for n in data.nic_requests if n.is_public)
            public_ip_name = get_ip_from_interface_name(request_to_connect_to_public_subnet.interface_name)
            data.public_ip_address = self._get_public_ip_address(network_client=network_client,
                                                                 azure_vm_deployment_model=deployment_model,
                                                                 group_name=data.group_name,
                                                                 cancellation_context=cancellation_context,
                                                                 ip_name=public_ip_name,
                                                                 logger=logger)

        deployed_app_attributes = self._prepare_deployed_app_attributes(
            admin_username=data.vm_credentials.admin_username,
            admin_password=data.vm_credentials.admin_password,
            public_ip=data.public_ip_address)

        # check if CustomImageDataModel or MarketplaceImageDataModel, no more options
        is_market_place = type(data.image_model) is MarketplaceImageDataModel
        vm_details_data = self.vm_details_provider.create(vm, is_market_place, logger, network_client, data.group_name)

        deploy_result = DeployAppResult(vmUuid=vm.vm_id,
                                        vmName=data.vm_name,
                                        deployedAppAddress=data.primary_private_ip_address,
                                        deployedAppAttributes=deployed_app_attributes,
                                        vmDetailsData=vm_details_data)

        return deploy_result

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
            nics=data.nics,
            region=cloud_provider_model.region,
            vm_name=data.vm_name,
            tags=data.tags,
            vm_size=data.vm_size,
            cancellation_context=cancellation_context,
            disk_size=deployment_model.disk_size,
            logger=logger)

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
            nics=data.nics,
            region=cloud_provider_model.region,
            vm_name=data.vm_name,
            tags=data.tags,
            vm_size=data.vm_size,
            purchase_plan=data.image_model.purchase_plan,  # type should be MarketplaceImageDataModel
            cancellation_context=cancellation_context,
            disk_size=deployment_model.disk_size)

    def _get_nic_requests(self, network_client, cloud_provider_model, logger, deployment_model, resource_group_name,
                          vm_name):
        """
        Get request to connect nic to subnet (contains subnet, interface name, and private/public
        This method will acquire the subnets connected to the sandbox virtual network, then associate them with a
        NicRequest, which also contains the interface name as well as if the network is public or not.

        Furthermore, the nic requests are ordered by the device index, i.e. Nics are created according to the order the
        user wanted the subnets to be connected.

        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient
        :param cloud_provider_model: cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel
        :param logger: logging.Logger instance
        :rtype: list[NicRequest]
        :param BaseDeployAzureVMResourceModel deployment_model:
        """

        multiple_subnet_mode = hasattr(deployment_model, 'network_configurations') \
                               and deployment_model.network_configurations

        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(
            network_client=network_client,
            group_name=cloud_provider_model.management_group_name)

        [logger.warn('existing subnet name: ' + s.name) for s in sandbox_virtual_network.subnets]

        nic_requests = []

        # in default subnet mode, there are no special network configurations, i.e. no ConnectToSubnet actions
        # in this case, PrepareSandboxInfra creates a single default subnet for sandbox.

        if not multiple_subnet_mode:
            try:
                nic_requests = [next((NicRequest("{}-{}".format(vm_name, 0), s, is_public=True)
                                      for s in sandbox_virtual_network.subnets if resource_group_name in s.name), None)]

            except StopIteration:
                logger.error("Subnets were not found under the resource group {}".format(
                    cloud_provider_model.management_group_name))
                raise Exception("Could not find a valid subnet.")

        # in multiple subnet mode, the server has sent network actions to perform,
        # we will return the subnets needed by this deployment; first we check if the subnets were created by a previous
        # stage, PrepareSandboxInfra, then we match them to ConnectSubnetActions sent by server.

        else:
            # when there are multiple subnets, they have an order based on device index; the device index is either
            # arbitrary, or set by user specifically by configuring blueprint connection attribute
            # "Source/TargetRequestVnic"

            # sort network requests
            deployment_model.network_configurations.sort(key=lambda x: x.connection_params.device_index)

            # subnet ids for subnets we need to connect and were already created in a previous phase
            request_subnet_ids = [action.connection_params.subnet_id
                                  for action in deployment_model.network_configurations]

            logger.warn('requested subnet names: ')
            [logger.warn(subnet_id) for subnet_id in request_subnet_ids]

            try:
                for i, connect_action in enumerate(deployment_model.network_configurations):
                    subnet_id = connect_action.connection_params.subnet_id
                    subnet = next((subnet for subnet in sandbox_virtual_network.subnets if subnet.name == subnet_id),
                                  None)
                    if subnet:
                        nic_requests.append(NicRequest(
                            "{}-{}".format(vm_name, i),
                            subnet,
                            connect_action.connection_params.is_public_subnet()
                        ))

            except StopIteration:
                logger.error("Subnets were not found under the resource group {}".format(
                    cloud_provider_model.management_group_name))
                raise Exception("Could not find a valid subnet.")

        return nic_requests

    def _rollback_deployed_resources(self, logger, compute_client, network_client, group_name, nic_requests, vm_name,
                                     private_ip_allocation_method, allocated_private_ips, reservation_id,
                                     cloudshell_session):
        """
        Remove all created resources by Deploy VM operation on any Exception.
        This method doesnt support cancellation because full cleanup is mandatory for successful deletion of subnet
        during cleanup-connectivity.

        :param compute_client: azure.mgmt.compute.compute_management_client.ComputeManagementClient
        :param network_client: azure.mgmt.network.network_management_client.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param nic_requests: list[NicRequest]
        :param vm_name: Azure VM resource name
        :param logger: logging.Logger instance
        :param IPAllocationMethod private_ip_allocation_method
        :param list[str] allocated_private_ips:
        :param CloudShellAPISession cloudshell_session:
        :return:
        """
        logger.info("Delete VM {} ".format(vm_name))
        self.vm_service.delete_vm(compute_management_client=compute_client,
                                  group_name=group_name,
                                  vm_name=vm_name)

        for nic_request in nic_requests:
            ip_name = get_ip_from_interface_name(nic_request.interface_name)
            logger.info("Delete NIC {} ".format(nic_request.interface_name))
            self.network_service.delete_nic(network_client=network_client,
                                            group_name=group_name,
                                            interface_name=nic_request.interface_name)

            logger.info("Delete IP {} ".format(ip_name))
            self.network_service.delete_ip(network_client=network_client,
                                           group_name=group_name,
                                           ip_name=ip_name)

        if is_static_allocation(private_ip_allocation_method):
            try:
                self.ip_service.release_ips(logger, cloudshell_session, reservation_id, allocated_private_ips)
            except:
                logger.exception('Failed to released ips from pool')

        self.network_service.delete_nsg_artifacts_associated_with_vm(
            network_client=network_client,
            resource_group_name=group_name,
            vm_name=vm_name)

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
                                  storage_client, cancellation_context, cloudshell_session):
        """ Creates and configures common VM objects: NIC, Credentials, NSG (if needed)

        :param cloudshell_session:
        :param DeployAzureVMOperation.DeployDataModel data:
        :param BaseDeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param logging.Logger logger:
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param azure.mgmt.network.network_management_client.StorageManagementClient storage_client:
        :param CancellationContext cancellation_context:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cloudshell_session:
        :return: Updated DeployDataModel instance
        :rtype: DeployAzureVMOperation.DeployDataModel
        """

        # 1. Create network security group for VM
        #       -   Open traffic to VM on inbound ports (an attribute on the app)
        #       -   Open traffic to VM from additional mgmt networks
        #       -   Open traffic to VM from mgmt vnet
        #       -   block traffic to VM from sandbox if "allow all sandbox traffic = false"
        subnets_nsg_name = self.security_group_service.get_subnets_nsg_name(data.reservation_id)
        vm_nsg = self._create_vm_network_security_group(cancellation_context, cloud_provider_model, data,
                                                        deployment_model, logger, network_client)

        inbound_rules = RulesAttributeParser.parse_port_group_attribute(deployment_model.inbound_ports)
        for rule in inbound_rules:
            rule.name = "{0}_inbound_ports".format(data.vm_name.replace(" ", ""))

        subnet_nsg_lock = self.generic_lock_provider.get_resource_lock(lock_key=subnets_nsg_name, logger=logger)

        # 3. Create network for vm
        data.nics = []
        for i, nic_request in enumerate(data.nic_requests):
            logger.info("Creating NIC '{}'".format(nic_request.interface_name))
            ip_name = get_ip_from_interface_name(nic_request.interface_name)
            add_public_ip = deployment_model.add_public_ip and nic_request.is_public
            nic = self.network_service.create_network_for_vm(network_client=network_client,
                                                             group_name=data.group_name,
                                                             interface_name=nic_request.interface_name,
                                                             ip_name=ip_name,
                                                             cloud_provider_model=cloud_provider_model,
                                                             subnet=nic_request.subnet,
                                                             add_public_ip=add_public_ip,
                                                             public_ip_type=deployment_model.public_ip_type,
                                                             tags=data.tags,
                                                             logger=logger,
                                                             network_security_group=vm_nsg,
                                                             reservation_id=data.reservation_id,
                                                             cloudshell_session=cloudshell_session)

            private_ip_address = nic.ip_configurations[0].private_ip_address

            data.all_private_ip_addresses.append(private_ip_address)
            if i == 0:
                data.primary_private_ip_address = private_ip_address

            logger.info("NIC private IP is {}".format(data.primary_private_ip_address))
            data.nics.append(nic)

            # once we have the NIC ip, we can create a permissive security rule for inbound ports but only to ip
            # inbound ports only works on public subnets! private subnets are allowed all traffic from sandbox
            # but no traffic from public addresses.
            if nic_request.is_public:
                logger.info("Adding inbound port rules to sandbox subnets NSG, with ip address as destination {0}"
                            .format(private_ip_address))
                self.security_group_service.create_network_security_group_rules(network_client,
                                                                                data.group_name,
                                                                                subnets_nsg_name,
                                                                                inbound_rules,
                                                                                private_ip_address,
                                                                                subnet_nsg_lock,
                                                                                start_from=1000)

        # 5. Prepare credentials for VM
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

    def _create_vm_network_security_group(self, cancellation_context, cloud_provider_model, data, deployment_model,
                                          logger, network_client):

        # Purpose of method is create a network security group that handles inbound and outbound traffic for a specific
        # app.
        # All nics on the VM are affected by the rules set on the VM

        management_vnet_cidr = self._get_management_vnet_cidr(cloud_provider_model, network_client)
        self.network_service.get_sandbox_virtual_network(network_client, data.group_name)

        # create network security group
        security_group_name = 'NSG_' + data.vm_name
        tags = self.tags_service.get_tags(data.vm_name, data.reservation)
        vm_nsg = self.security_group_service.create_network_security_group(network_client=network_client,
                                                                           group_name=data.group_name,
                                                                           security_group_name=security_group_name,
                                                                           region=cloud_provider_model.region,
                                                                           tags=tags)
        vm_nsg_lock = self.generic_lock_provider.get_resource_lock(lock_key=security_group_name, logger=logger)

        #   VM NSG rules overview
        #       1xxx
        #       -   Open traffic to VM on inbound ports (an attribute on the app)
        #       3xxx
        #       -   Open traffic to VM from additional mgmt networks
        #       4080
        #       -   Open traffic to VM from mgmt vnet
        #       4090
        #       -   block traffic to VM from sandbox if "allow all sandbox traffic = false"

        # Rule 1xxx
        if deployment_model.inbound_ports:
            inbound_rules = RulesAttributeParser.parse_port_group_attribute(
                ports_attribute=deployment_model.inbound_ports)

            self.security_group_service.create_network_security_group_rules(network_client,
                                                                            data.group_name,
                                                                            security_group_name,
                                                                            inbound_rules,
                                                                            destination_addr='*',
                                                                            lock=vm_nsg_lock,
                                                                            start_from=1000)

        # Rule 3xxx:
        # Open traffic to VM from additional mgmt networks

        for mgmt_network in cloud_provider_model.additional_mgmt_networks:
            security_rule_name = 'Allow_{0}'.format(mgmt_network.replace('/', '-'))
            allow_traffic_from_additional_mgmt_network = [
                RuleData(protocol=SecurityRuleProtocol.asterisk,
                         port='*',
                         access=SecurityRuleAccess.allow,
                         name=security_rule_name)]

            self.security_group_service.create_network_security_group_rules(network_client,
                                                                            data.group_name,
                                                                            security_group_name,
                                                                            allow_traffic_from_additional_mgmt_network,
                                                                            '*',
                                                                            vm_nsg_lock,
                                                                            start_from=3000)

        # Rule 4070:
        # Open traffic to VM from mgmt vnet

        security_rule_name = 'Allow_Traffic_From_Management_Vnet_To_Any'
        allow_all_traffic = [RuleData(protocol=SecurityRuleProtocol.asterisk,
                                      port='*',
                                      access=SecurityRuleAccess.allow,
                                      name=security_rule_name)]

        self.security_group_service.create_network_security_group_rules(
            network_client,
            data.group_name,
            security_group_name,
            allow_all_traffic,
            destination_addr="*",
            lock=vm_nsg_lock,
            start_from=4070,
            source_address=management_vnet_cidr
        )

        # Rule 4080 / Rule 4090:
        # Block traffic from sandbox if vm is set to allow all sandbox traffic = false;
        # And if block traffic from sandbox, must specifically allow traffic for AzureLoadBalancer, otherwise basic
        # services will break

        if not deployment_model.allow_all_sandbox_traffic or deployment_model.allow_all_sandbox_traffic == 'False':
            security_rule_name = 'Allow_Azure_Load_Balancer'
            allow_all_traffic = [RuleData(protocol=SecurityRuleProtocol.asterisk,
                                          port='*',
                                          access=SecurityRuleAccess.allow,
                                          name=security_rule_name)]

            self.security_group_service.create_network_security_group_rules(
                network_client,
                data.group_name,
                security_group_name,
                allow_all_traffic,
                destination_addr="*",
                lock=vm_nsg_lock,
                start_from=4080,
                source_address="AzureLoadBalancer"
            )

            security_rule_name = 'Deny_Sandbox_Traffic'
            deny_all_traffic = [RuleData(protocol=SecurityRuleProtocol.asterisk,
                                         port='*',
                                         access=SecurityRuleAccess.deny,
                                         name=security_rule_name)]

            self.security_group_service.create_network_security_group_rules(
                network_client,
                data.group_name,
                security_group_name,
                deny_all_traffic,
                destination_addr="*",
                lock=vm_nsg_lock,
                start_from=4090,
                source_address="VirtualNetwork"
            )

        self.cancellation_service.check_if_cancelled(cancellation_context)
        return vm_nsg

    def _get_management_vnet_cidr(self, cloud_provider_model, network_client):
        virtual_networks = self.network_service.get_virtual_networks(network_client=network_client,
                                                                     group_name=cloud_provider_model.management_group_name)
        management_vnet = self.network_service.get_virtual_network_by_tag(virtual_networks,
                                                                          NetworkService.NETWORK_TYPE_TAG_NAME,
                                                                          NetworkService.MGMT_NETWORK_TAG_VALUE)
        management_vnet_cidr = management_vnet.address_space.address_prefixes[0]
        return management_vnet_cidr

    def _validate_deployment_model(self, vm_deployment_model, os_type, network_actions):
        """
        :param list[ConnectSubnet] network_actions:
        :param BaseDeployAzureVMResourceModel vm_deployment_model:
        :param OperatingSystemTypes image_os_type: (enum) windows/linux value os_type
        """

        # if there are only private subnets, and we ask for public ip, that is a problem:

        all_subnets_are_private = network_actions and all(s.actionParams.subnetServiceAttributes['Public'] == 'False'
                                                          for s in network_actions if s.actionParams and
                                                          s.actionParams.subnetServiceAttributes and
                                                          'Public' in s.actionParams.subnetServiceAttributes)

        if all_subnets_are_private and vm_deployment_model.add_public_ip:
            raise ValueError("Cannot deploy app with public ip when connected only to private subnets")

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

        deployed_app_attr = [Attribute('Password', admin_password),
                             Attribute('User', admin_username),
                             Attribute('Public IP', public_ip)]

        return deployed_app_attr

    def _prepare_deploy_data(self, logger, reservation, deployment_model, cloud_provider_model,
                             network_client, storage_client, compute_client, network_actions):
        """
        :param logging.Logger logger:
        :param ReservationModel reservation:
        :param BaseDeployAzureVMResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model: cloud provider
        :param azure.mgmt.network.network_management_client.NetworkManagementClient network_client:
        :param azure.mgmt.storage.storage_management_client.StorageManagementClient storage_client:
        :param azure.mgmt.storage.storage_management_client.ComputeManagementClient compute_client:
        :param list[ConnectSubnet] network_actions:
        :return:
        :rtype: DeployAzureVMOperation.DeployDataModel
        """

        image_data_model = self.image_data_factory.get_image_data_model(
            cloud_provider_model=cloud_provider_model,
            deployment_model=deployment_model,
            compute_client=compute_client,
            logger=logger)

        self._validate_deployment_model(vm_deployment_model=deployment_model,
                                        os_type=image_data_model.os_type,
                                        network_actions=network_actions)

        data = self.DeployDataModel()

        data.reservation_id = str(reservation.reservation_id)
        data.reservation = reservation
        data.group_name = str(reservation.reservation_id)
        data.image_model = image_data_model

        # normalize the app name to a valid Azure vm name
        data.app_name = self.name_provider_service.normalize_name(deployment_model.app_name)

        resource_postfix = self.name_provider_service.generate_short_unique_string()
        unique_resource_name = self.name_provider_service.generate_name(name=data.app_name,
                                                                        postfix=resource_postfix,
                                                                        max_length=64)
        data.vm_name = unique_resource_name
        data.computer_name = self._prepare_computer_name(name=data.app_name,
                                                         postfix=resource_postfix,
                                                         os_type=data.image_model.os_type)

        data.vm_size = self._prepare_vm_size(azure_vm_deployment_model=deployment_model,
                                             cloud_provider_model=cloud_provider_model)

        logger.warn("Retrieve sandbox subnet {}".format(data.group_name))
        data.nic_requests = self._get_nic_requests(network_client=network_client,
                                                   cloud_provider_model=cloud_provider_model,
                                                   logger=logger,
                                                   deployment_model=deployment_model,
                                                   resource_group_name=data.group_name,
                                                   vm_name=unique_resource_name)

        logger.warn('interfaces:' + str(len(data.nic_requests)))
        logger.info("Retrieve sandbox storage account name by resource group {}".format(data.group_name))
        data.storage_account_name = self.storage_service.get_sandbox_storage_account_name(storage_client=storage_client,
                                                                                          group_name=data.group_name)

        data.tags = self.tags_service.get_tags(vm_name=data.vm_name, reservation=reservation)
        logger.info("Tags for the VM {}".format(data.tags))

        return data

    class DeployDataModel(object):
        def __init__(self):
            self.reservation_id = ''  # type: str
            self.reservation = None  # type: ReservationModel
            self.app_name = ''  # type: str
            self.group_name = ''  # type: str
            self.computer_name = ''  # type: str
            self.vm_name = ''  # type: str
            self.vm_size = ''  # type: str
            self.storage_account_name = ''  # type: str
            self.tags = {}  # type: dict
            self.image_model = None  # type: ImageDataModelBase
            self.os_type = ''  # type: OperatingSystemTypes
            self.nic = None  # type: NetworkInterface
            self.vm_credentials = None  # type: VMCredentials
            self.primary_private_ip_address = ''  # type: str
            self.all_private_ip_addresses = []  # type: list[str]
            self.public_ip_address = ''  # type: str
            self.nic_requests = []  # type: list[NicRequest]


def get_ip_from_interface_name(interface_name):
    ip_name = interface_name + '_PublicIP'
    return ip_name
