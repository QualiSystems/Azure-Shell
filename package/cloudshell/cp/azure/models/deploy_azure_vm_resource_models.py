from typing import Dict, List


class BaseDeployAzureVMResourceModel(object):
    def __init__(self):
        self.vm_size = ''  # type: str
        self.disk_size = ''  # type: str
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
        self.disk_type = ''  # type: str
        self.allow_all_sandbox_traffic = True  # type: bool


class DeployARMTemplateResourceModel():
    def __init__(self):
        self.template_url = ''  # type: str
        self.parameters = ''  # type: Dict[str, str]


class RouteResourceModel(object):
    def __init__(self):
        self.name = ''
        self.route_address_prefix = ''
        self.next_hop_type = ''
        self.next_hope_address = ''


class RouteTableRequestResourceModel(object):
    def __init__(self):
        self.name = None  # type: str
        self.routes = []  # type: List[RouteResourceModel]
        self.subnets = []


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
        self.image_name = ""
        self.image_resource_group = ""
