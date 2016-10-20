class RuleData(object):
    def __init__(self, protocol, priority, port=None, from_port=None, to_port=None):
        """

        :param from_port: (int) to_port-start port
        :param to_port: (int) from_port-end port
        :param port: (int) single port
        :param protocol: (str) protocol-can be UDP or TCP
        :param priority (int) rule priority
        :return:
        """
        self.protocol = protocol
        self.priority = priority
        self.port = port
        self.from_port = from_port
        self.to_port = to_port
