class RuleData(object):
    def __init__(self, protocol, port=None, from_port=None, to_port=None, access="Allow", name=None):
        """

        :type name: str override SecurityRule name with this string
        :param from_port: (int) to_port-start port
        :param to_port: (int) from_port-end port
        :param port: (int) single port
        :param protocol: (str) protocol-can be UDP or TCP
        :return:
        """
        self.access = access
        self.protocol = protocol
        self.port = port
        self.from_port = from_port
        self.to_port = to_port
        self.name = name

    def __repr__(self):
        repr_string = super(RuleData, self).__repr__()
        return "{} With attrs: {}".format(repr_string, self.__dict__)
