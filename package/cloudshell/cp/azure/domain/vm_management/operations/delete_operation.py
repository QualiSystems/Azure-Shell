from azure.mgmt.network.models import Subnet
from msrestazure.azure_exceptions import CloudError


class DeleteAzureVMOperation(object):
    def __init__(self,
                 vm_service,
                 network_service,
                 tags_service):
        """

        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :return:
        """

        self.vm_service = vm_service
        self.network_service = network_service
        self.tags_service = tags_service

    def remove_nsg_from_subnet(self, network_client, resource_group_name, cloud_provider_model):
        management_group_name = cloud_provider_model.management_group_name

        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(network_client=network_client,
                                                                                   group_name=management_group_name,
                                                                                   tags_service=self.tags_service)

        subnet = next((subnet for subnet in sandbox_virtual_network.subnets if subnet.name == resource_group_name),
                      None)

        if subnet is None:
            raise Exception("Could not find a valid subnet.")

        subnet.network_security_group = None

        self.network_service.update_subnet(network_client, management_group_name, sandbox_virtual_network.name,
                                           subnet.name, subnet)

    def delete_resource_group(self, resource_client, group_name):

        try:
            self.vm_service.delete_resource_group(resource_management_client=resource_client, group_name=group_name)
        except Exception as e:
            raise e

    def delete_sandbox_subnet(self, network_client, cloud_provider_model, resource_group_name):
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(network_client=network_client,
                                                                                   group_name=cloud_provider_model.management_group_name,
                                                                                   tags_service=self.tags_service)
        subnet = next((subnet for subnet in sandbox_virtual_network.subnets if subnet.name == resource_group_name),
                      None)
        if subnet is None:
            raise Exception("Could not find a valid subnet.")

        network_client.subnets.delete(cloud_provider_model.management_group_name, sandbox_virtual_network.name,
                                      subnet.name)

    def delete(self, compute_client, network_client, group_name, vm_name, logger):
        """
        :param group_name:
        :param network_client:
        :param vm_name: the same as ip_name and interface_name
        :param compute_client:
        :param logger:
        :return:
        """
        try:

            self.vm_service.delete_vm(compute_management_client=compute_client,
                                      group_name=group_name,
                                      vm_name=vm_name)

            self.network_service.delete_nic(network_client=network_client,
                                            group_name=group_name,
                                            interface_name=vm_name)

            self.network_service.delete_ip(network_client=network_client,
                                           group_name=group_name,
                                           ip_name=vm_name)

        except CloudError as e:
            if e.response.reason == "Not Found":
                logger.info('Deleting Azure VM Exception... ' + e.message)
            else:
                raise e
        except Exception as e:
            logger.info('Deleting Azure VM Exception...')
            raise e
