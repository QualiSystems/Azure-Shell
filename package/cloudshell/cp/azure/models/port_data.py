from azure.mgmt.network.models import RouteNextHopType


class PortData(object):
    def __init__(self, from_port, to_port, protocol, destination=None, source=RouteNextHopType.internet):
        """ec2_session

        :param port: to_port-start port
        :type port: int
        :param port: from_port-end port
        :type port: int
        :param protocol: protocol-can be UDP or TCP
        :type port: str
        :param destination: Determines the traffic that can leave your instance, and where it can go.
        :type port: str
        :return:
        """
        self.from_port = from_port
        self.to_port = to_port
        self.protocol = protocol
        self.destination = destination
        self.source = source
        self.name = None