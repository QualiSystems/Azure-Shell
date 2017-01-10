class BaseDeployAzureVMResourceModel(object):
    def __init__(self):
        self.group_name = ''  # type: str
        self.vm_name = ''  # type: str
        self.cloud_provider = ''  # type: str
        self.vm_size = ''  # type: str
        self.autoload = False  # type: bool
        self.add_public_ip = False  # type: bool
        self.inbound_ports = ''  # type: str
        self.public_ip_type = ''  # type: str
        self.app_name = ''  # type: str
        self.username = ''  # type: str
        self.password = ''  # type: str
        self.extension_script_file = ''
        self.extension_script_configurations = ''
        self.extension_script_timeout = 0  # type: int


class DeployAzureVMResourceModel(BaseDeployAzureVMResourceModel):
    def __init__(self):
        super(DeployAzureVMResourceModel, self).__init__()
        self.image_publisher = ''  # type: str
        self.image_offer = ''  # type: str
        self.image_sku = ''  # type: str
        self.image_version = ''  # type: str


class DeployAzureVMFromCustomImageResourceModel(BaseDeployAzureVMResourceModel):
    def __init__(self):
        super(DeployAzureVMFromCustomImageResourceModel, self).__init__()
        self.image_urn = ""
        self.image_os_type = ""
