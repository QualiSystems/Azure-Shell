class DeleteAzureVMOperation(object):
    def __init__(self,
                 logger,
                 vm_service,
                 network_service):
        """

        :param logger:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :return:
        """

        self.logger = logger
        self.vm_service = vm_service
        self.network_service = network_service

    def delete(self, compute_client, network_client, resource_group_name, vm_name):
        """
        :param vm_name:
        :param resource_group_name:
        :param compute_client:
        :return:
        """
        try:
            self.vm_service.delete_vm(compute_management_client=compute_client,
                                      resource_group_name=resource_group_name,
                                      vm_name=vm_name)

            self.network_service.delete_nic(network_client=network_client)

        except Exception as e:
            raise e
