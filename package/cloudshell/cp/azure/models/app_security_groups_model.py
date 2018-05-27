class AppSecurityGroupModel(object):
    def __init__(self):
        self.deployed_app = ''  # type: DeployedApp
        self.security_group_configurations = None  # type: list[SecurityGroupConfiguration]


class SecurityGroupConfiguration(object):
    def __init__(self):
        self.subnet_id = ''
        self.rules = None  # type: list[PortData]


class DeployedApp(object):
    def __init__(self):
        self.name = ''
        self.vm_details = ''  # type: VmDetails


class VmDetails(object):
    def __init__(self):
        self.uid = ''
