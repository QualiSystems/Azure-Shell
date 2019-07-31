from azure.mgmt.compute.models import OSProfile, HardwareProfile, NetworkProfile, \
    NetworkInterfaceReference, DiskCreateOptionTypes, ImageReference, OSDisk, \
    VirtualMachine, StorageProfile, Plan, ManagedDiskParameters, StorageAccountTypes, DiagnosticsProfile, \
    BootDiagnostics
from azure.mgmt.compute.models import OperatingSystemTypes, VirtualMachineImage
from azure.mgmt.compute.models.linux_configuration import LinuxConfiguration
from azure.mgmt.compute.models.ssh_configuration import SshConfiguration
from azure.mgmt.compute.models.ssh_public_key import SshPublicKey
from azure.mgmt.resource.resources.models import ResourceGroup
from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error, retryable_error_max_attempts, \
    retryable_wait_time, retry_if_retryable_error


class VirtualMachineService(object):
    SUCCEEDED_PROVISIONING_STATE = "Succeeded"

    def __init__(self, task_waiter_service):
        """

        :param task_waiter_service: package.cloudshell.cp.azure.domain.services.task_waiter.TaskWaiterService
        """
        self.task_waiter_service = task_waiter_service

    def get_active_vm(self, compute_management_client, group_name, vm_name):
        """Get VM from Azure and check if it exists and in "Succeeded" provisioning state

        :param compute_management_client: azure.mgmt.compute.ComputeManagementClient instance
        :param group_name: Azure resource group name (reservation id)
        :param vm_name: name for VM
        :return: azure.mgmt.compute.models.VirtualMachine
        """
        vm = self.get_vm(compute_management_client=compute_management_client,
                         group_name=group_name,
                         vm_name=vm_name)

        if vm.provisioning_state != self.SUCCEEDED_PROVISIONING_STATE:
            raise Exception("Can't perform action. Azure instance is not in active state")

        return vm

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_vm(self, compute_management_client, group_name, vm_name):
        """

        :param compute_management_client: azure.mgmt.compute.ComputeManagementClient instance
        :param group_name: Azure resource group name (reservation id)
        :param vm_name: name for VM
        :return: azure.mgmt.compute.models.VirtualMachine
        """

        return compute_management_client.virtual_machines.get(group_name, vm_name)

    def _prepare_linux_configuration(self, ssh_key):
        """Create LinuxConfiguration object with nested SshPublicKey object for Azure client

        :param ssh_key: cloudshell.cp.azure.models.authorized_key.AuthorizedKey instance
        :return: azure.mgmt.compute.models.linux_configuration.LinuxConfiguration instance
        """
        ssh_public_key = SshPublicKey(path=ssh_key.path_to_key, key_data=ssh_key.key_data)
        ssh_config = SshConfiguration(public_keys=[ssh_public_key])

        return LinuxConfiguration(disable_password_authentication=True, ssh=ssh_config)

    @retry(stop_max_attempt_number=5,
           wait_fixed=2000,
           retry_on_exception=retry_if_connection_error)
    @retry(stop_max_attempt_number=retryable_error_max_attempts,
           wait_fixed=retryable_wait_time,
           retry_on_exception=retry_if_retryable_error)
    def _create_vm(self, compute_management_client, region, group_name, vm_name, hardware_profile, network_profile,
                   os_profile, storage_profile, cancellation_context, tags, vm_plan=None, logger=None):
        """Create and deploy Azure VM from the given parameters

        :param compute_management_client: azure.mgmt.compute.compute_management_client.ComputeManagementClient
        :param region: (str) Azure region
        :param group_name: (str) resource group name (reservation id)
        :param vm_name: (str) Azure VM resource name
        :param hardware_profile: azure.mgmt.compute.models.HardwareProfile instance
        :param network_profile: azure.mgmt.compute.models.NetworkProfile instance
        :param os_profile: azure.mgmt.compute.models.OSProfile instance
        :param storage_profile: azure.mgmt.compute.models.StorageProfile instance
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :param tags: azure tags
        :rtype: azure.mgmt.compute.models.VirtualMachine
        """
        virtual_machine = VirtualMachine(location=region,
                                         tags=tags,
                                         os_profile=os_profile,
                                         hardware_profile=hardware_profile,
                                         network_profile=network_profile,
                                         storage_profile=storage_profile,
                                         diagnostics_profile=DiagnosticsProfile(
                                             boot_diagnostics=BootDiagnostics(enabled=False)),
                                         plan=vm_plan)

        if logger:
            logger.info('Created POCO VM for {0} in resource group {1}'.format(vm_name, group_name))

        operation_poller = compute_management_client.virtual_machines.create_or_update(group_name, vm_name,
                                                                                       virtual_machine)

        if logger:
            logger.info('Got poller for create VM task for {0} in resource group {1}'.format(vm_name, group_name))

        return self.task_waiter_service.wait_for_task(operation_poller=operation_poller,
                                                      cancellation_context=cancellation_context,
                                                      logger=logger)

    def _prepare_os_profile(self, vm_credentials, computer_name):
        """Prepare OS profile object for the VM

        :param cloudshell.cp.azure.models.vm_credentials.VMCredentials vm_credentials:
        :param str computer_name: computer name
        :return: OSProfile instance
        :rtype: azure.mgmt.compute.models.OSProfile
        """
        if vm_credentials.ssh_key:
            linux_configuration = self._prepare_linux_configuration(vm_credentials.ssh_key)
        else:
            linux_configuration = None

        return OSProfile(admin_username=vm_credentials.admin_username,
                         admin_password=vm_credentials.admin_password,
                         linux_configuration=linux_configuration,
                         computer_name=computer_name)

    def prepare_image_os_type(self, image_os_type):
        """Prepare Image OS Type object for the VM

        :param str image_os_type: (str) Image OS Type attribute ("Windows" or "Linux")
        :return: (enum) windows/linux value
        :rtype: azure.mgmt.compute.models.OperatingSystemTypes
        """
        if image_os_type.lower() == "linux":
            return OperatingSystemTypes.linux

        return OperatingSystemTypes.windows

    def create_vm_from_custom_image(self,
                                    compute_management_client,
                                    image_name,
                                    image_resource_group,
                                    disk_type,
                                    vm_credentials,
                                    computer_name,
                                    group_name,
                                    nics,
                                    region,
                                    vm_name,
                                    tags,
                                    vm_size,
                                    cancellation_context,
                                    disk_size,
                                    logger):

        """Create VM from custom image URN

        :param cancellation_context:
        :param str vm_size: Azure instance type
        :param azure.mgmt.compute.ComputeManagementClient compute_management_client: instance
        :param str image_name: Azure custom image name
        :param str image_resource_group: Azure resource group
        :param str disk_type: Disk type (HDD/SDD)
        :param cloudshell.cp.azure.models.vm_credentials.VMCredentials vm_credentials:
        :param str computer_name: computer name
        :param str group_name: Azure resource group name (reservation id)
        :param list nics: list[Nic]
        :param str region: Azure region
        :param str vm_name: name for VM
        :param tags: Azure tags
        :return:
        :rtype: azure.mgmt.compute.models.VirtualMachine
        """

        os_profile = self._prepare_os_profile(vm_credentials=vm_credentials,
                                              computer_name=computer_name)

        logger.info('Prepared OS Profile for {0} in resource group {1}'.format(vm_name, group_name))

        hardware_profile = HardwareProfile(vm_size=vm_size)

        logger.info('Prepared OS Profile for {0} in resource group {1}'.format(vm_name, group_name))

        network_interfaces = [NetworkInterfaceReference(id=nic.id) for nic in nics]
        for network_interface in network_interfaces:
            network_interface.primary = False
        network_interfaces[0].primary = True

        logger.info('Prepared {2} network interfaces for {0} in resource group {1}'.format(vm_name, group_name, len(network_interfaces)))

        network_profile = NetworkProfile(network_interfaces=network_interfaces)

        logger.info('Prepared Network Profile for {0} in resource group {1}'.format(vm_name, group_name))

        image = compute_management_client.images.get(resource_group_name=image_resource_group, image_name=image_name)
        storage_profile = StorageProfile(
                os_disk=self._prepare_os_disk(disk_type, disk_size),
                image_reference=ImageReference(id=image.id))

        logger.info('Prepared Storage Profile for {0} in resource group {1}'.format(vm_name, group_name))

        logger.info('Before actual create vm for {0} in resource group {1}'.format(vm_name, group_name))

        return self._create_vm(
                compute_management_client=compute_management_client,
                region=region,
                group_name=group_name,
                vm_name=vm_name,
                hardware_profile=hardware_profile,
                network_profile=network_profile,
                os_profile=os_profile,
                storage_profile=storage_profile,
                cancellation_context=cancellation_context,
                tags=tags,
                logger=logger)

    def _get_storage_type(self, disk_type):
        """
        Converts disk_type string value (HDD/SSD) to the azure storage type
        :param str disk_type:
        :return:
        :rtype: StorageAccountTypes
        """
        disk_type = disk_type.upper().strip()
        if disk_type == "HDD":
            return StorageAccountTypes.standard_lrs
        if disk_type == "SSD":
            return StorageAccountTypes.premium_lrs
        return None  # return None so that default azure api value will be used

    def create_vm_from_marketplace(self,
                                   compute_management_client,
                                   image_offer,
                                   image_publisher,
                                   image_sku,
                                   image_version,
                                   disk_type,
                                   vm_credentials,
                                   computer_name,
                                   group_name,
                                   nics,
                                   region,
                                   vm_name,
                                   tags,
                                   vm_size,
                                   purchase_plan,
                                   cancellation_context,
                                   disk_size):
        """

        :param vm_size: (str) Azure instance type
        :param compute_management_client: azure.mgmt.compute.ComputeManagementClient instance
        :param image_offer: (str) image offer
        :param image_publisher: (str) image publisher
        :param image_sku: (str) image SKU
        :param image_version: (str) image version
        :param str disk_type: Disk type (HDD/SDD)
        :param vm_credentials: cloudshell.cp.azure.models.vm_credentials.VMCredentials instance
        :param computer_name: computer name
        :param group_name: Azure resource group name (reservation id)
        :param nic_id: Azure network id
        :param region: Azure region
        :param vm_name: name for VM
        :param tags: Azure tags
        :param purchase_plan: PurchasePlan
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :rtype: azure.mgmt.compute.models.VirtualMachine
        """
        os_profile = self._prepare_os_profile(vm_credentials=vm_credentials,
                                              computer_name=computer_name)

        hardware_profile = HardwareProfile(vm_size=vm_size)

        network_interfaces = [NetworkInterfaceReference(id=nic.id) for nic in nics]
        for network_interface in network_interfaces:
            network_interface.primary = False
        network_interfaces[0].primary = True
        network_profile = NetworkProfile(network_interfaces=network_interfaces)

        storage_profile = StorageProfile(
                os_disk=self._prepare_os_disk(disk_type, disk_size),
                image_reference=ImageReference(publisher=image_publisher,
                                               offer=image_offer,
                                               sku=image_sku,
                                               version=image_version))

        vm_plan = None
        if purchase_plan is not None:
            vm_plan = Plan(name=purchase_plan.name, publisher=purchase_plan.publisher, product=purchase_plan.product)

        return self._create_vm(
                compute_management_client=compute_management_client,
                region=region,
                group_name=group_name,
                vm_name=vm_name,
                hardware_profile=hardware_profile,
                network_profile=network_profile,
                os_profile=os_profile,
                storage_profile=storage_profile,
                cancellation_context=cancellation_context,
                tags=tags,
                vm_plan=vm_plan)

    def _prepare_os_disk(self, disk_type, disk_size):
        """
        :param str disk_type:
        :param str disk_size:
        :return:
        :rtype: OSDisk
        """
        if disk_size.isdigit():
            disk_size_num = int(disk_size)
            if disk_size_num > 1023:
                raise Exception('Disk size cannot be larger than 1023 GB')
            return OSDisk(create_option=DiskCreateOptionTypes.from_image,
                          disk_size_gb=disk_size_num,
                          managed_disk=ManagedDiskParameters(storage_account_type=self._get_storage_type(disk_type)))
        return \
            OSDisk(create_option=DiskCreateOptionTypes.from_image,
                   managed_disk=ManagedDiskParameters(
                           storage_account_type=self._get_storage_type(disk_type)))

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_resource_group(self, resource_management_client, group_name, region, tags):
        return resource_management_client.resource_groups.create_or_update(group_name,
                                                                           ResourceGroup(location=region, tags=tags))

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_resource_group(self, resource_management_client, group_name):
        """

        :param resource_management_client: cloudshell.cp.azure.common.azure_clients.ResourceManagementClient instance
        :param group_name: (str) the name of the resource group on Azure
        :return: azure.mgmt.resource.resources.models.ResourceGroup instance
        """
        return resource_management_client.resource_groups.get(resource_group_name=group_name)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_resource_group(self, resource_management_client, group_name):
        result = resource_management_client.resource_groups.delete(group_name)
        result.wait()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_vm(self, compute_management_client, group_name, vm_name):
        """

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_management_client:
        :param group_name:
        :param vm_name:
        :return:
        """
        result = compute_management_client.virtual_machines.delete(resource_group_name=group_name,
                                                                   vm_name=vm_name)
        result.wait()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def start_vm(self, compute_management_client, group_name, vm_name, async=False):
        """Start Azure VM instance

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_management_client:
        :param group_name: The name of the resource group.
        :param vm_name: The name of the virtual machine.
        :param async: (bool) whether wait for VM operation result or not
        :return:
        """
        operation_poller = compute_management_client.virtual_machines.start(resource_group_name=group_name,
                                                                            vm_name=vm_name)
        if not async:
            return operation_poller.result()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def stop_vm(self, compute_management_client, group_name, vm_name, async=False):
        """Stop Azure VM instance

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_management_client:
        :param group_name: The name of the resource group.
        :param vm_name: The name of the virtual machine.
        :param async: (bool) whether wait for VM operation result or not
        :return:
        """
        async_vm_deallocate = compute_management_client.virtual_machines.deallocate(resource_group_name=group_name,
                                                                                    vm_name=vm_name)
        if not async:
            async_vm_deallocate.wait()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_virtual_machine_image(self, compute_management_client, location, publisher_name, offer, skus):
        """Get operation system from the given image

        :param compute_management_client: azure.mgmt.compute.compute_management_client.ComputeManagementClient
        :param location: (str) Azure region
        :param publisher_name: (str) Azure publisher name
        :param offer: (str) Azure Image offer
        :param skus: (str) Azure Image SKU
        :return: Virtual Machine Image
        :rtype: VirtualMachineImage
        """
        # get last version first (required for the virtual machine images GET Api)
        image_resources = compute_management_client.virtual_machine_images.list(
                location=location,
                publisher_name=publisher_name,
                offer=offer,
                skus=skus)

        version = image_resources[-1].name

        deployed_image = compute_management_client.virtual_machine_images.get(
                location=location,
                publisher_name=publisher_name,
                offer=offer,
                skus=skus,
                version=version)

        return deployed_image

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def list_virtual_machine_sizes(self, compute_management_client, location):
        """List available virtual machine sizes within given location

        :param compute_management_client: azure.mgmt.compute.compute_management_client.ComputeManagementClient
        :param location: (str) Azure region
        :return: azure.mgmt.compute.models.VirtualMachineSizePaged instance
        """
        return compute_management_client.virtual_machine_sizes.list(location=location)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_managed_disk(self, compute_management_client, resource_group, disk_name):
        """ Will delete the provided managed disk

        :param azure.mgmt.compute.ComputeManagementClient compute_management_client:
        :param str resource_group:
        :param str disk_name:
        :return:
        """
        operation = compute_management_client.disks.delete(resource_group_name=resource_group, disk_name=disk_name)
        return operation.result()
