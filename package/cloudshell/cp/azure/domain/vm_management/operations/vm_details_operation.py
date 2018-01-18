from cloudshell.cp.azure.domain.common.vm_details_provider import VmDetailsProvider, VmDetails
from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService


class VmDetailsOperation(object):
    def __init__(self, vm_service, vm_details_provider):
        """
        :type vm_service: cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService
        :type vm_details_provider: cloudshell.cp.azure.domain.common.vm_details_provider.VmDetailsProvider
        """
        self.vm_service = vm_service
        self.vm_details_provider = vm_details_provider

    def get_vm_details(self, compute_client, group_name, vm_name, is_market_place, logger, network_client):
        """
        :param network_client:
        :param compute_client: azure.mgmt.compute.ComputeManagementClient instance
        :param group_name: Azure resource group name (reservation id)
        :param vm_name: name for VM
        :param is_market_place: bool
        :param logging.Logger logger:
        :return: cloudshell.cp.azure.domain.common.vm_details_provider.VmDetails
        """

        vm = self.vm_service.get_vm(compute_client, group_name, vm_name)
        return self.vm_details_provider.create(vm, is_market_place, logger, network_client, group_name)
