from functools import partial
from threading import Lock

from azure.mgmt.network.models import VirtualNetwork, Subnet
from msrestazure.azure_exceptions import CloudError


class DeleteAzureVMOperation(object):
    def __init__(self,
                 vm_service,
                 network_service,
                 tags_service,
                 security_group_service,
                 storage_service,
                 generic_lock_provider,
                 subnet_locker):
        """
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.lock_service.GenericLockProvider generic_lock_provider:
        :param threading.Lock subnet_locker:
        :return:
        """
        self.vm_service = vm_service
        self.network_service = network_service
        self.tags_service = tags_service
        self.security_group_service = security_group_service
        self.storage_service = storage_service
        self.subnet_locker = subnet_locker
        self.generic_lock_provider = generic_lock_provider

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

        remove_nsg_from_subnet_command = partial(self.remove_nsg_from_subnet,
                                                 network_client=network_client,
                                                 cloud_provider_model=cloud_provider_model,
                                                 resource_group_name=resource_group_name,
                                                 logger=logger)

        delete_sandbox_subnet_command = partial(self.delete_sandbox_subnet,
                                                network_client=network_client,
                                                cloud_provider_model=cloud_provider_model,
                                                resource_group_name=resource_group_name,
                                                logger=logger)

        delete_resource_group_command = partial(self.delete_resource_group,
                                                resource_client=resource_client,
                                                group_name=resource_group_name,
                                                logger=logger)

        """
        The order of execution is very important and it should be:
        1. remove nsg from subnet
        2. delete resource group
        3. delete sandbox subnet
        """
        errors = []
        for command in (remove_nsg_from_subnet_command, delete_resource_group_command, delete_sandbox_subnet_command):
            try:
                command()
            except Exception as e:
                logger.exception("Error in cleanup connectivity. Error: ")
                errors.append(e.message)

        if errors:
            result['success'] = False
            result['errorMessage'] = 'CleanupConnectivity ended with the error(s): {}'.format(errors)

        # release the generic lock for reservation in context
        self.generic_lock_provider.remove_lock_resource(resource_group_name, logger=logger)

        return result

    def remove_nsg_from_subnet(self, network_client, resource_group_name, cloud_provider_model, logger):
        logger.info("Removing NSG from the subnet...")

        management_group_name = cloud_provider_model.management_group_name
        logger.info("Retrieving sandbox vNet from MGMT group {}".format(management_group_name))
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(network_client=network_client,
                                                                                   group_name=management_group_name)

        subnet = self._find_sandbox_subnet(resource_group_name, sandbox_virtual_network)
        if subnet is None:
            logger.warning("Could not find subnet {} in resource group {} to detach NSG".format(
                resource_group_name, management_group_name))
            return

        subnet.network_security_group = None

        """
        # This call is atomic because we have to sync subnet updating for the entire sandbox vnet
        """
        with self.subnet_locker:
            logger.info("Updating subnet {} with NSG set to null".format(subnet.name))
            self.network_service.update_subnet(network_client, management_group_name, sandbox_virtual_network.name,
                                               subnet.name, subnet)

    def delete_resource_group(self, resource_client, group_name, logger):
        logger.info("Deleting resource group {0}.".format(group_name))
        self.vm_service.delete_resource_group(resource_management_client=resource_client, group_name=group_name)
        logger.info("Deleted resource group {0}.".format(group_name))

    def delete_sandbox_subnet(self, network_client, cloud_provider_model, resource_group_name, logger):
        logger.info("Deleting sandbox subnet...")

        logger.info("Retrieving sandbox vNet from MGMT group {}".format(cloud_provider_model.management_group_name))
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(
            network_client=network_client,
            group_name=cloud_provider_model.management_group_name)

        subnet = self._find_sandbox_subnet(resource_group_name, sandbox_virtual_network)

        if subnet is None:
            logger.warning("Could not find subnet {} in resource group {} to delete it".format(
                resource_group_name, cloud_provider_model.management_group_name))
            return

        with self.subnet_locker:
            logger.info("Deleting subnet {}".format(subnet.name))
            self.network_service.delete_subnet(network_client=network_client,
                                               group_name=cloud_provider_model.management_group_name,
                                               vnet_name=sandbox_virtual_network.name,
                                               subnet_name=subnet.name)
            logger.info("Deleted subnet {}".format(subnet.name))

    def _find_sandbox_subnet(self, resource_group_name, sandbox_virtual_network):
        """
        find the sandbox subnet in the vnet
        :param str resource_group_name:
        :param VirtualNetwork sandbox_virtual_network:
        :return:
        :rtype: Subnet
        """
        subnet = next((subnet for subnet in sandbox_virtual_network.subnets if subnet.name == resource_group_name),
                      None)
        return subnet

    def _delete_security_rules(self, network_client, group_name, vm_name, logger):
        """
        Delete NSG rules for given VM

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) The name of the resource group
        :param vm_name: (str) the same as ip_name and interface_name
        :param logger: logging.Logger instance
        :return:
        """
        logger.info("Deleting security group rules...")
        lock = self.generic_lock_provider.get_resource_lock(lock_key=group_name, logger=logger)
        self.security_group_service.delete_security_rules(network_client=network_client,
                                                          resource_group_name=group_name,
                                                          vm_name=vm_name,
                                                          lock=lock,
                                                          logger=logger)

    def _delete_vhd_disk(self, storage_client, group_name, vhd_url, logger):
        """Delete VHD Disk Blob resource on the azure for given VM

        :param group_name: (str) The name of the resource group
        :param vhd_url: (str) Blob VHD Disk URL
        :param logger: logging.Logger instance
        :return:
        """
        logger.info("Deleting VHD Disk {}...".format(vhd_url))
        url_model = self.storage_service.parse_blob_url(blob_url=vhd_url)

        self.storage_service.delete_blob(storage_client=storage_client,
                                         group_name=group_name,
                                         storage_name=url_model.storage_name,
                                         container_name=url_model.container_name,
                                         blob_name=url_model.blob_name)

    def _delete_vm(self, compute_client, group_name, vm_name, logger):
        """Delete VM resource on the azure

        :param compute_client: azure.mgmt.compute.ComputeManagementClient instance
        :param group_name: (str) The name of the resource group
        :param vm_name: (str) the same as ip_name and interface_name
        :param logger: logging.Logger instance
        :return:
        """
        logger.info("Deleting VM {}...".format(vm_name))
        self.vm_service.delete_vm(compute_management_client=compute_client,
                                  group_name=group_name,
                                  vm_name=vm_name)

    def _delete_nic(self, network_client, group_name, vm_name, logger):
        """Delete NIC resource on the azure for given VM

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) The name of the resource group
        :param vm_name: (str) the same as ip_name and interface_name
        :param logger: logging.Logger instance
        :return:
        """
        logger.info("Deleting Interface {}...".format(vm_name))
        self.network_service.delete_nic(network_client=network_client,
                                        group_name=group_name,
                                        interface_name=vm_name)

    def _delete_public_ip(self, network_client, group_name, vm_name, logger):
        """Delete Public IP resource on the azure for given VM

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) The name of the resource group
        :param vm_name: (str) the same as ip_name and interface_name
        :param logger: logging.Logger instance
        :return:
        """
        logger.info("Deleting Public IP {}...".format(vm_name))
        self.network_service.delete_ip(network_client=network_client,
                                       group_name=group_name,
                                       ip_name=vm_name)

    def delete(self, compute_client, network_client, storage_client, group_name, vm_name, logger):
        """Delete VM and all related resources

        :param compute_client: azure.mgmt.compute.ComputeManagementClient instance
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param storage_client: azure.mgmt.storage.StorageManagementClient instance
        :param group_name: (str) The name of the resource group
        :param vm_name: (str) the same as ip_name and interface_name
        :param logger: logging.Logger instance
        :return:
        """
        delete_security_rules_command = partial(self._delete_security_rules,
                                                network_client=network_client,
                                                group_name=group_name,
                                                vm_name=vm_name,
                                                logger=logger)

        delete_vm_command = partial(self._delete_vm,
                                    compute_client=compute_client,
                                    group_name=group_name,
                                    vm_name=vm_name,
                                    logger=logger)

        delete_nic_command = partial(self._delete_nic,
                                     network_client=network_client,
                                     group_name=group_name,
                                     vm_name=vm_name,
                                     logger=logger)

        delete_public_ip_command = partial(self._delete_public_ip,
                                           network_client=network_client,
                                           group_name=group_name,
                                           vm_name=vm_name,
                                           logger=logger)

        commands = [delete_security_rules_command, delete_vm_command, delete_nic_command, delete_public_ip_command]

        try:
            vm = self.vm_service.get_vm(compute_management_client=compute_client,
                                        group_name=group_name,
                                        vm_name=vm_name)
        except CloudError:
            logger.warning("Can't get VM to retrieve its VHD URL", exc_info=1)
        else:
            delete_vhd_disk_command = partial(self._delete_vhd_disk,
                                              storage_client=storage_client,
                                              group_name=group_name,
                                              vhd_url=vm.storage_profile.os_disk.vhd.uri,
                                              logger=logger)

            commands.append(delete_vhd_disk_command)

        for command in commands:
            try:
                command()
            except CloudError as e:
                if e.response.reason == "Not Found":
                    logger.info('Deleting Azure VM Not Found Exception:', exc_info=1)
                else:
                    logger.exception('Deleting Azure VM Exception:')
                    raise
            except Exception:
                logger.exception('Deleting Azure VM Exception:')
                raise
