import traceback

from azure.mgmt.network.models import Subnet
from msrestazure.azure_exceptions import CloudError
from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error


class DeleteAzureVMOperation(object):
    def __init__(self,
                 vm_service,
                 network_service,
                 tags_service,
                 security_group_service):
        """
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :return:
        """

        self.vm_service = vm_service
        self.network_service = network_service
        self.tags_service = tags_service
        self.security_group_service = security_group_service

    def cleanup_connectivity(self, network_client, resource_client, cloud_provider_model, resource_group_name, logger):
        """
        :param logger:
        :param network_client:
        :param resource_client:
        :param cloud_provider_model:
        :param resource_group_name:
        """
        logger.info("Start Cleanup Connectivity operation")
        result = {'success': True}

        try:
            logger.info("Removing NSG from the subnet...")
            self.remove_nsg_from_subnet(network_client=network_client, cloud_provider_model=cloud_provider_model,
                                        resource_group_name=resource_group_name,
                                        logger=logger)

            logger.info("Deleting sandbox subnet...")
            self.delete_sandbox_subnet(network_client=network_client, cloud_provider_model=cloud_provider_model,
                                       resource_group_name=resource_group_name,
                                       logger=logger)

            logger.info("Deleting resource group...")
            self.delete_resource_group(resource_client=resource_client, group_name=resource_group_name)

        except Exception as ex:
            logger.exception("Error in cleanup connectivity. Error: ")
            result['success'] = False
            result['errorMessage'] = 'CleanupConnectivity ended with the error: {0}'.format(ex.message)

        return result

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def remove_nsg_from_subnet(self, network_client, resource_group_name, cloud_provider_model, logger):
        management_group_name = cloud_provider_model.management_group_name

        logger.info("Retrieving sandbox vNet from MGMT group {}".format(management_group_name))
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(network_client=network_client,
                                                                                   group_name=management_group_name,
                                                                                   tags_service=self.tags_service)

        subnet = next((subnet for subnet in sandbox_virtual_network.subnets if subnet.name == resource_group_name),
                      None)

        if subnet is None:
            logger.error("Could not find subnet {} in resource group {} to delete it".format(
                resource_group_name, management_group_name))

            raise Exception("Could not find a valid subnet.")

        subnet.network_security_group = None

        logger.info("Updating subnet {} with NSG set to null".format(subnet.name))
        self.network_service.update_subnet(network_client, management_group_name, sandbox_virtual_network.name,
                                           subnet.name, subnet)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_resource_group(self, resource_client, group_name):
        self.vm_service.delete_resource_group(resource_management_client=resource_client, group_name=group_name)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_sandbox_subnet(self, network_client, cloud_provider_model, resource_group_name, logger):
        logger.info("Retrieving sandbox vNet from MGMT group {}".format(cloud_provider_model.management_group_name))
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(network_client=network_client,
                                                                                   group_name=cloud_provider_model.management_group_name,
                                                                                   tags_service=self.tags_service)

        subnet = next((subnet for subnet in sandbox_virtual_network.subnets if subnet.name == resource_group_name),
                      None)
        if subnet is None:
            logger.error("Could not find subnet {} in resource group {} to delete it".format(
                resource_group_name, cloud_provider_model.management_group_name))

            raise Exception("Could not find a valid subnet.")

        network_client.subnets.delete(cloud_provider_model.management_group_name, sandbox_virtual_network.name,
                                      subnet.name)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
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
            logger.info("Deleting security group rules...")
            self.security_group_service.delete_security_rules(network_client=network_client,
                                                              resource_group_name=group_name,
                                                              vm_name=vm_name)

            logger.info("Deleting VM {}...".format(vm_name))
            self.vm_service.delete_vm(compute_management_client=compute_client,
                                      group_name=group_name,
                                      vm_name=vm_name)

            logger.info("Deleting Interface {}...".format(vm_name))
            self.network_service.delete_nic(network_client=network_client,
                                            group_name=group_name,
                                            interface_name=vm_name)

            logger.info("Deleting Public IP {}...".format(vm_name))
            self.network_service.delete_ip(network_client=network_client,
                                           group_name=group_name,
                                           ip_name=vm_name)

        except CloudError as e:
            if e.response.reason == "Not Found":
                logger.info('Deleting Azure VM Exception:', exc_info=1)
            else:
                logger.exception('Deleting Azure VM Exception:')
                raise
        except Exception:
            logger.exception('Deleting Azure VM Exception:')
            raise
