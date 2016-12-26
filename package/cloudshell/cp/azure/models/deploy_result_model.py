class DeployResult(object):
    def __init__(self, vm_name, vm_uuid, cloud_provider_resource_name, autoload, auto_delete,
                 auto_power_off, inbound_ports, deployed_app_attributes,
                 deployed_app_address, public_ip, resource_group):
        """
        :param str vm_name: The name of the virtual machine
        :param uuid uuid: The UUID
        :param str cloud_provider_resource_name: The Cloud Provider resource name
        :param boolean auto_power_off:
        :param boolean wait_for_ip: issue 285: "wait for IP" should be always set to false in the deploy result
        :param boolean auto_delete:
        :param boolean autoload:
        :param str inbound_ports:
        :param [dict] deployed_app_attributes:
        :param str deployed_app_address:
        :param str public_ip:
        :return:
        """

        self.resource_group = resource_group
        self.inbound_ports = inbound_ports
        self.vm_name = vm_name
        self.vm_uuid = vm_uuid
        self.cloud_provider_resource_name = cloud_provider_resource_name
        self.auto_power_off = auto_power_off
        self.wait_for_ip = False
        self.auto_delete = auto_delete
        self.autoload = autoload
        self.deployed_app_attributes = deployed_app_attributes
        self.deployed_app_address = deployed_app_address
        self.public_ip = public_ip


