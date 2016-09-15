from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService
from cloudshell.cp.azure.models.deploy_result_model import DeployResult


class DeployAzureVMOperation(object):
    def __init__(self,
                 logger,
                 vm_service):
        """

        :param logger:
        :param VirtualMachineService vm_service:
        :return:
        """

        self.logger = logger
        self.vm_service = vm_service

    def deploy(self, azure_vm_deployment_model, cloud_provider_model):
        # inputs from attributes?
        resource_name = ""
        group_name = ""
        region = ""
        image_publisher = 'Canonical'
        image_offer = 'UbuntuServer'
        image_sku = '16.04.0-LTS'
        image_version = 'latest'

        admin_username = 'gil1'
        interface_name = 'gil6'
        network_name = 'gil7'
        subnet_name = 'gil8'
        ip_name = 'gil9'

        storage_account_name = 'gil4'
        computer_name = 'gil3'
        admin_password = 'ScJaw12deDFG'  # Auto generated?
        vm_name = resource_name  # will be created in real time?
        storage_name = 'gil4'

        # 2. Create a storage account
        self.vm_service.create_storage_account(group_name, region, storage_account_name)

        # 3. Create the network interface using a helper function (defined below)
        nic_id = self.vm_service.create_network(group_name, interface_name, ip_name, network_name, region, subnet_name)

        # 4. create Vm
        self.vm_service.create_vm(image_offer, image_publisher, image_sku, image_version, admin_password,
                                  admin_username,
                                  computer_name, group_name, nic_id, region, storage_name, vm_name)

        return DeployResult()
