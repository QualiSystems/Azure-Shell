class DeployAzureVMResourceModel(object):
    def __init__(self):
        self.group_name = ''  # type: str
        self.vm_name = ''  # type: str
        self.cloud_provider = ''  # type: str
        self.instance_type = ''  # type: str
        self.wait_for_ip = False  # type: bool
        self.autoload = False  # type: bool
        self.add_public_ip = False  # type: bool
        self.inbound_ports = ''  # type: str
        self.outbound_ports = ''  # type: str
        self.public_ip_type = ''  # type: str
        self.image_publisher = ''  # type: str
        self.image_offer = ''  # type: str
        self.image_sku = ''  # type: str
        self.disk_type = ''  # type: str

