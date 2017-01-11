class RuleData(object):
    def __init__(self, protocol, port=None, from_port=None, to_port=None):
        """

        :param from_port: (int) to_port-start port
        :param to_port: (int) from_port-end port
        :param port: (int) single port
        :param protocol: (str) protocol-can be UDP or TCP
        :return:
        """
        self.protocol = protocol
        self.port = port
        self.from_port = from_port
        self.to_port = to_port

    def __repr__(self):
        repr_string = super(RuleData, self).__repr__()
        return "{} With attrs: {}".format(repr_string, self.__dict__)
