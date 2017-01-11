from azure.mgmt.compute.models import OSProfile, HardwareProfile, NetworkProfile, \
    NetworkInterfaceReference, CachingTypes, DiskCreateOptionTypes, VirtualHardDisk, ImageReference, OSDisk, \
    VirtualMachine, StorageProfile, Plan
from azure.mgmt.compute.models.linux_configuration import LinuxConfiguration
from azure.mgmt.compute.models.ssh_configuration import SshConfiguration
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.compute.models.ssh_public_key import SshPublicKey
from azure.mgmt.compute.models import OperatingSystemTypes, VirtualMachineImage
from msrestazure.azure_exceptions import CloudError
from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error


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

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def _create_vm(self, compute_management_client, region, group_name, vm_name, hardware_profile, network_profile,
                   os_profile, storage_profile, cancellation_context, tags, vm_plan=None):
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
                                         plan=vm_plan)

        operation_poller = compute_management_client.virtual_machines.create_or_update(group_name, vm_name,
                                                                                       virtual_machine)

        return self.task_waiter_service.wait_for_task(operation_poller=operation_poller,
                                                      cancellation_context=cancellation_context)

    def _prepare_os_profile(self, vm_credentials, computer_name):
        """Prepare OS profile object for the VM

        :param vm_credentials: cloudshell.cp.azure.models.vm_credentials.VMCredentials instance
        :param computer_name: (str) computer name
        :return: azure.mgmt.compute.models.OSProfile instance
        """
        if vm_credentials.ssh_key:
            linux_configuration = self._prepare_linux_configuration(vm_credentials.ssh_key)
        else:
            linux_configuration = None

        return OSProfile(admin_username=vm_credentials.admin_username,
                         admin_password=vm_credentials.admin_password,
                         linux_configuration=linux_configuration,
                         computer_name=computer_name)

    def _prepare_vhd(self, storage_name, vm_name):
        """Prepare VHD object for the VM

        :param storage_name: (str) storage account name
        :param vm_name: (str) VM name
        :return: azure.mgmt.compute.models.VirtualHardDisk instance
        """
        vhd_format = 'https://{}.blob.core.windows.net/vhds/{}.vhd'.format(storage_name, vm_name)
        return VirtualHardDisk(uri=vhd_format)

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
                                    image_urn,
                                    image_os_type,
                                    vm_credentials,
                                    computer_name,
                                    group_name,
                                    nic_id,
                                    region,
                                    storage_name,
                                    vm_name,
                                    tags,
                                    vm_size,
                                    cancellation_context):
        """Create VM from custom image URN

        :param cancellation_context:
        :param vm_size: (str) Azure instance type
        :param compute_management_client: azure.mgmt.compute.ComputeManagementClient instance
        :param image_urn: Azure custom image URL
        :param image_os_type: azure.mgmt.compute.models.OperatingSystemTypes OS type (linux/windows)
        :param vm_credentials: cloudshell.cp.azure.models.vm_credentials.VMCredentials instance
        :param computer_name: computer name
        :param group_name: Azure resource group name (reservation id)
        :param nic_id: Azure network id
        :param region: Azure region
        :param storage_name: Azure storage name
        :param vm_name: name for VM
        :param tags: Azure tags
        :return:
        :rtype: azure.mgmt.compute.models.VirtualMachine
        """
        os_profile = self._prepare_os_profile(vm_credentials=vm_credentials,
                                              computer_name=computer_name)

        hardware_profile = HardwareProfile(vm_size=vm_size)
        network_profile = NetworkProfile(network_interfaces=[NetworkInterfaceReference(id=nic_id)])

        vhd = self._prepare_vhd(storage_name, vm_name)
        image = VirtualHardDisk(uri=image_urn)

        os_disk = OSDisk(os_type=image_os_type,
                         caching=CachingTypes.none,
                         create_option=DiskCreateOptionTypes.from_image,
                         name=storage_name,
                         vhd=vhd,
                         image=image)

        storage_profile = StorageProfile(os_disk=os_disk)

        try:
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
                    tags=tags)
        except CloudError as exc:
            error = str(exc)
            if "OSProvisioningTimedOut".lower() in error.lower():
                raise Exception(error + "\r\n"
                                        "You may have a mismatch between the selected 'Image OS Type' and the "
                                        "operation system provided in the 'Image URN'.")
            raise

    def create_vm_from_marketplace(self,
                                   compute_management_client,
                                   image_offer,
                                   image_publisher,
                                   image_sku,
                                   image_version,
                                   vm_credentials,
                                   computer_name,
                                   group_name,
                                   nic_id,
                                   region,
                                   storage_name,
                                   vm_name,
                                   tags,
                                   vm_size,
                                   purchase_plan,
                                   cancellation_context):
        """

        :param vm_size: (str) Azure instance type
        :param compute_management_client: azure.mgmt.compute.ComputeManagementClient instance
        :param image_offer: (str) image offer
        :param image_publisher: (str) image publisher
        :param image_sku: (str) image SKU
        :param image_version: (str) image version
        :param vm_credentials: cloudshell.cp.azure.models.vm_credentials.VMCredentials instance
        :param computer_name: computer name
        :param group_name: Azure resource group name (reservation id)
        :param nic_id: Azure network id
        :param region: Azure region
        :param storage_name: Azure storage name
        :param vm_name: name for VM
        :param tags: Azure tags
        :param purchase_plan: PurchasePlan
        :param cancellation_context cloudshell.shell.core.driver_context.CancellationContext instance
        :rtype: azure.mgmt.compute.models.VirtualMachine
        """
        os_profile = self._prepare_os_profile(vm_credentials=vm_credentials,
                                              computer_name=computer_name)

        hardware_profile = HardwareProfile(vm_size=vm_size)

        network_profile = NetworkProfile(network_interfaces=[NetworkInterfaceReference(id=nic_id)])

        vhd = self._prepare_vhd(storage_name, vm_name)

        os_disk = OSDisk(caching=CachingTypes.none,
                         create_option=DiskCreateOptionTypes.from_image,
                         name=storage_name,
                         vhd=vhd)

        image_reference = ImageReference(publisher=image_publisher, offer=image_offer, sku=image_sku,
                                         version=image_version)

        storage_profile = StorageProfile(os_disk=os_disk, image_reference=image_reference)

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
        operation_poller = compute_management_client.virtual_machines.power_off(resource_group_name=group_name,
                                                                                vm_name=vm_name)
        if not async:
            return operation_poller.result()

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
