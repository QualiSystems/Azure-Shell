from cloudshell.cp.azure.models.network_actions_models import ConnectToSubnetActionResult


class DeployResult(object):
    def __init__(self, vm_name, vm_uuid, cloud_provider_resource_name, autoload,
                 inbound_ports, deployed_app_attributes, deployed_app_address,
                 public_ip, resource_group, extension_time_out, vm_details_data, network_configuration_results):
        """
        :param str vm_name: The name of the virtual machine
        :param uuid uuid: The UUID
        :param str cloud_provider_resource_name: The Cloud Provider resource name
        :param boolean autoload:
        :param str inbound_ports:
        :param [dict] deployed_app_attributes:
        :param str deployed_app_address:
        :param str public_ip:
        :param bool extension_time_out:
        :param list[ConnectToSubnetActionResult] network_configuration_results:
        :return:
        """

        self.resource_group = resource_group
        self.inbound_ports = inbound_ports
        self.vm_name = vm_name
        self.vm_uuid = vm_uuid
        self.cloud_provider_resource_name = cloud_provider_resource_name
        self.auto_power_off = False
        self.wait_for_ip = False
        self.auto_delete = True
        self.autoload = autoload
        self.deployed_app_attributes = deployed_app_attributes
        self.deployed_app_address = deployed_app_address
        self.public_ip = public_ip
        self.extension_time_out = extension_time_out
        self.vm_details_data = vm_details_data
        self.network_configuration_results = network_configuration_results  # type: list[ConnectToSubnetActionResult]
