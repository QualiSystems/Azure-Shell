class NicRequest(object):
    def __init__(self, interface_name, subnet, is_public):
        """
        A request for connecting a subnet to a VM nic
        :param interface_name: str
        :param subnet: azure.mgmt.network.models.Subnet
        :param is_public: bool
        :return:
        """
        self.interface_name = interface_name
        self.subnet = subnet
        self.is_public = is_public
