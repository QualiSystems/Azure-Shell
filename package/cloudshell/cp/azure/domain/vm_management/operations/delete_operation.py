import traceback
from functools import partial

from azure.mgmt.network.models import VirtualNetwork, Subnet
from cloudshell.api.cloudshell_api import CloudShellAPISession
from msrestazure.azure_exceptions import CloudError

from cloudshell.cp.azure.common.helpers.ip_allocation_helper import is_static_allocation
from cloudshell.cp.azure.domain.services.ip_service import IpService


class DeleteAzureVMOperation(object):
    def __init__(self, vm_service, network_service, tags_service, security_group_service, storage_service,
                 generic_lock_provider, subnet_locker, ip_service):
        """
        :param ip_service:
        :param cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService vm_service:
        :param cloudshell.cp.azure.domain.services.network_service.NetworkService network_service:
        :param cloudshell.cp.azure.domain.services.tags.TagService tags_service:
        :param cloudshell.cp.azure.domain.services.security_group.SecurityGroupService security_group_service:
        :param cloudshell.cp.azure.domain.services.storage_service.StorageService storage_service:
        :param cloudshell.cp.azure.domain.services.lock_service.GenericLockProvider generic_lock_provider:
        :param threading.Lock subnet_locker:
        :param cloudshell.cp.azure.domain.services.ip_service.IpService ip_service:
        :return:
        """
        self.vm_service = vm_service
        self.network_service = network_service
        self.tags_service = tags_service
        self.security_group_service = security_group_service
        self.storage_service = storage_service
        self.subnet_locker = subnet_locker
        self.generic_lock_provider = generic_lock_provider
        self.ip_service = ip_service

    def cleanup_connectivity(self, network_client, resource_client, cloud_provider_model,
                             resource_group_name, request, logger):
        """
        :param request:
        :param logger:
        :param network_client:
        :param resource_client:
        :param cloud_provider_model:
        :param resource_group_name:
        """
        logger.info("Start Cleanup Connectivity operation")
        result = {'success': True,
                  'actionId': next(iter(filter(lambda x: x.type == "cleanupNetwork", request.actions))).actionId}

        remove_nsg_from_subnets_command = partial(self.remove_nsg_and_routetable_from_subnets,
                                                  network_client=network_client,
                                                  cloud_provider_model=cloud_provider_model,
                                                  resource_group_name=resource_group_name,
                                                  logger=logger)

        delete_sandbox_subnets_command = partial(self.delete_sandbox_subnets,
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
        for command in (remove_nsg_from_subnets_command, delete_resource_group_command, delete_sandbox_subnets_command):
            try:
                command()
            except Exception as e:
                logger.exception("Error in cleanup connectivity. Error: ")
                errors.append(e.message)

        if errors:
            result['success'] = False
            result['errorMessage'] = 'CleanupSandboxInfra ended with the error(s): {}'.format(errors)

        # release the generic lock for reservation in context
        self.generic_lock_provider.remove_lock_resource(resource_group_name, logger)
        self.generic_lock_provider.remove_lock_resource(IpService.SANDBOX_LOCK_KEY.format(resource_group_name), logger)

        return result

    def remove_nsg_and_routetable_from_subnets(self, network_client, resource_group_name, cloud_provider_model, logger):
        logger.info("Removing NSG from the sandbox subnets...")

        management_group_name = cloud_provider_model.management_group_name
        logger.info("Retrieving sandbox vNet from MGMT group {}".format(management_group_name))
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(network_client=network_client,
                                                                                   group_name=management_group_name)

        subnets = self._find_sandbox_subnets(resource_group_name, sandbox_virtual_network)
        if not subnets:
            logger.warning("Could not find subnets in sandbox {} to detach NSG".format(resource_group_name))
            return

        for subnet in subnets:
            subnet.network_security_group = None
            subnet.route_table = None
            """
            # This call is atomic because we have to sync subnet updating for the entire sandbox vnet
            """
            with self.subnet_locker:
                logger.info("Updating subnet {} with NSG set to null".format(subnet.name))
                self.network_service.update_subnet(network_client=network_client,
                                                   resource_group_name=management_group_name,
                                                   virtual_network_name=sandbox_virtual_network.name,
                                                   subnet_name=subnet.name,
                                                   subnet=subnet)

    def delete_resource_group(self, resource_client, group_name, logger):
        logger.info("Deleting resource group {0}.".format(group_name))
        self.vm_service.delete_resource_group(resource_management_client=resource_client, group_name=group_name)
        logger.info("Deleted resource group {0}.".format(group_name))

    def delete_sandbox_subnets(self, network_client, cloud_provider_model, resource_group_name, logger):
        logger.info("Deleting sandbox subnets...")

        logger.info("Retrieving sandbox vNet from MGMT group {}".format(cloud_provider_model.management_group_name))
        sandbox_virtual_network = self.network_service.get_sandbox_virtual_network(
            network_client=network_client,
            group_name=cloud_provider_model.management_group_name)

        subnets = self._find_sandbox_subnets(resource_group_name, sandbox_virtual_network)

        if not subnets:
            logger.warning("Could not find subnets in vnet {} for sandbox {} to delete it".format(
                sandbox_virtual_network.name, resource_group_name))
            return

        for subnet in subnets:
            with self.subnet_locker:
                logger.info("Deleting subnet {}".format(subnet.name))
                self.network_service.delete_subnet(network_client=network_client,
                                                   group_name=cloud_provider_model.management_group_name,
                                                   vnet_name=sandbox_virtual_network.name,
                                                   subnet_name=subnet.name)
                logger.info("Deleted subnet {}".format(subnet.name))

    def _find_sandbox_subnets(self, resource_group_name, sandbox_virtual_network):
        """
        find the sandbox subnet in the vnet
        :param str resource_group_name:
        :param VirtualNetwork sandbox_virtual_network:
        :return:
        :rtype: list[Subnet]
        """
        return [subnet for subnet in sandbox_virtual_network.subnets
                if subnet.name.startswith(resource_group_name)]

    def _delete_vm_disk(self, logger, storage_client, compute_client, group_name, vm):
        """Delete the VM data disk. Will delete VHD or Managed Disk of the VM.

        :param logging.Logger logger:
        :param azure.mgmt.storage.StorageManagementClient storage_client:
        :param azure.mgmt.compute.ComputeManagementClient compute_client:
        :param str group_name:
        :param azure.mgmt.compute.models.VirtualMachine vm:
        :return:
        """
        if vm.storage_profile.os_disk.vhd:
            self._delete_vhd_disk(storage_client=storage_client,
                                  group_name=group_name,
                                  logger=logger,
                                  vhd_url=vm.storage_profile.os_disk.vhd.uri)
        elif vm.storage_profile.os_disk.managed_disk:
            self._delete_managed_disk(logger=logger,
                                      compute_client=compute_client,
                                      group_name=group_name,
                                      managed_disk_name=vm.storage_profile.os_disk.name)
        else:
            raise ValueError("Supported os data disk not found in VM {0} so cannot delete data disk".format(vm.name))

    def _delete_managed_disk(self, logger, compute_client, group_name, managed_disk_name):
        """ Will delete the provided managed disk

        :param logging.Logger logger:
        :param azure.mgmt.compute.ComputeManagementClient compute_client:
        :param str group_name:
        :param str managed_disk_name:
        :return:
        """
        logger.info("Deleting managed Disk {0} in resource group {1}...".format(managed_disk_name, group_name))
        result = self.vm_service.delete_managed_disk(compute_management_client=compute_client,
                                                     resource_group=group_name,
                                                     disk_name=managed_disk_name)
        logger.debug("{}", result)

    def _delete_vhd_disk(self, storage_client, group_name, vhd_url, logger):
        """Delete VHD Disk Blob resource on the azure for given VM

        :param azure.mgmt.storage.StorageManagementClient storage_client:
        :param str group_name: The name of the resource group
        :param str vhd_url: Blob VHD Disk URL
        :param logging.Logger logger:
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

    def _delete_nics(self, network_client, group_name, vm_name, logger, interface_names):
        """Delete NIC resource on the azure for given VM

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) The name of the resource group
        :param vm_name: (str) the same as ip_name and interface_name
        :param logger: logging.Logger instance
        :param interface_names: list(str)
        :return:
        """
        logger.info("Deleting Interface {}...".format(vm_name))
        self.network_service.delete_nics(network_client=network_client,
                                         group_name=group_name,
                                         interface_names=interface_names)

    def _delete_public_ip(self, network_client, group_name, vm_name, logger, public_ip_names):
        """Delete Public IP resource on the azure for given VM

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: (str) The name of the resource group
        :param vm_name: (str) the same as ip_name and interface_name
        :param logger: logging.Logger instance
        :return:
        """
        logger.info("Deleting Public IP {}...".format(vm_name))
        self.network_service.delete_ips(network_client=network_client,
                                        group_name=group_name,
                                        public_ip_names=public_ip_names)

    def delete(self, compute_client, network_client, storage_client, group_name, vm_name, logger, cloudshell_session):
        """Delete VM and all related resources

        :param azure.mgmt.compute.ComputeManagementClient compute_client:
        :param azure.mgmt.network.NetworkManagementClient network_client:
        :param azure.mgmt.storage.StorageManagementClient storage_client:
        :param group_name: (str) The name of the resource group
        :param vm_name: (str) the same as ip_name and interface_name
        :param logger: logging.Logger instance
        :param CloudShellAPISession cloudshell_session:
        :return:
        """

        vm = compute_client.virtual_machines.get(group_name, vm_name)
        network_interface_names = [nir.id.split('/')[-1] for nir in vm.network_profile.network_interfaces]
        network_interfaces = [network_client.network_interfaces.get(group_name, nin) for nin in network_interface_names]
        public_ip_names = [ni.ip_configurations[0].public_ip_address.id.split('/')[-1] for ni in network_interfaces
                           if len(ni.ip_configurations) > 0 and
                           hasattr(ni.ip_configurations[0], 'public_ip_address') and
                           ni.ip_configurations[0].public_ip_address is not None]
        private_ips = [nic.ip_configurations[0].private_ip_address for nic in network_interfaces
                       if
                       is_static_allocation(nic.ip_configurations[0].private_ip_allocation_method)]

        delete_vm_command = partial(self._delete_vm,
                                    compute_client=compute_client,
                                    group_name=group_name,
                                    vm_name=vm_name,
                                    logger=logger)

        delete_nics_command = partial(self._delete_nics,
                                      network_client=network_client,
                                      group_name=group_name,
                                      vm_name=vm_name,
                                      logger=logger,
                                      interface_names=network_interface_names)

        delete_public_ip_command = partial(self._delete_public_ip,
                                           network_client=network_client,
                                           group_name=group_name,
                                           vm_name=vm_name,
                                           logger=logger,
                                           public_ip_names=public_ip_names)

        commands = [delete_vm_command,
                    delete_nics_command,
                    delete_public_ip_command]

        try:
            vm = self.vm_service.get_vm(compute_management_client=compute_client,
                                        group_name=group_name,
                                        vm_name=vm_name)

        except CloudError:
            logger.warning("Can't get VM to retrieve its VHD URL", exc_info=1)

        else:
            delete_vhd_disk_command = partial(self._delete_vm_disk,
                                              logger=logger,
                                              storage_client=storage_client,
                                              compute_client=compute_client,
                                              group_name=group_name,
                                              vm=vm)

            commands.append(delete_vhd_disk_command)

        for command in commands:
            try:
                command()
            except CloudError as e:
                if e.response.reason == "Not Found":
                    logger.info('Deleting Azure Resource Not Found Exception:', exc_info=1)
                    logger.info(e.message)
                else:
                    logger.exception('Deleting Azure VM Exception:')
                    raise
            except Exception:
                logger.exception('Deleting Azure VM Exception:')
                raise

        self.network_service.delete_nsg_artifacts_associated_with_vm(
            network_client=network_client,
            resource_group_name=group_name,
            vm_name=vm_name)

        # try releasing private ip address that were statically allocated
        try:
            if private_ips:
                self.ip_service.release_ips(logger, cloudshell_session, group_name, private_ips)
        except:
            logger.warning('Error while trying to release private ips: {}. Error: {}'.format(','.join(private_ips),
                                                                                             traceback.format_exc()))

