from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error


class PowerAzureVMOperation(object):
    def __init__(self, vm_service):
        """
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :return:
        """
        self.vm_service = vm_service

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def power_on(self, compute_client, resource_group_name, vm_name):
        """Power on Azure VM instance

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param resource_group_name: The name of the resource group.
        :param vm_name: The name of the virtual machine.
        :return
        """
        return self.vm_service.start_vm(compute_client, resource_group_name, vm_name)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def power_off(self, compute_client, resource_group_name, vm_name):
        """Power off Azure VM instance

        :param azure.mgmt.compute.compute_management_client.ComputeManagementClient compute_client:
        :param resource_group_name: The name of the resource group.
        :param vm_name: The name of the virtual machine.
        :return
        """
        return self.vm_service.stop_vm(compute_client, resource_group_name, vm_name)
