import re

from cloudshell.cp.azure.models.rule_data import RuleData


class RulesAttributeParser(object):
    @staticmethod
    def parse_port_group_attribute(ports_attribute):
        """
        :param ports_attribute:
        :param last_priority:
        :return: list[RuleData]
        :rtype: list[RuleData]
        """
        splitted_ports = filter(None, ports_attribute.strip().split(';'))

        return [
            RulesAttributeParser._single_port_parse(port.strip())
            for port in splitted_ports]

    @staticmethod
    def _single_port_parse(ports_attribute):
        from_port = 'from_port'
        to_port = 'to_port'
        protocol = 'protocol'
        tcp = 'tcp'

        from_to_protocol_match = re.match(r"^((?P<from_port>\d+)-(?P<to_port>\d+):(?P<protocol>(udp|tcp)))$",
                                          ports_attribute, flags=re.IGNORECASE)

        # 80-50000:udp
        if from_to_protocol_match:
            from_port = from_to_protocol_match.group(from_port)
            to_port = from_to_protocol_match.group(to_port)
            protocol = from_to_protocol_match.group(protocol).lower()
            name = "inbound_port_"
            return RuleData(protocol=protocol, from_port=from_port, to_port=to_port)

        from_protocol_match = re.match(r"^((?P<from_port>\d+):(?P<protocol>(udp|tcp)))$", ports_attribute,
                                       flags=re.IGNORECASE)

        # 80:udp
        if from_protocol_match:
            port = from_protocol_match.group(from_port)
            protocol = from_protocol_match.group(protocol).lower()
            return RuleData(protocol=protocol, port=port)

        from_to_match = re.match(r"^((?P<from_port>\d+)-(?P<to_port>\d+))$", ports_attribute)

        # 20-80
        if from_to_match:
            from_port = from_to_match.group(from_port)
            to_port = from_to_match.group(to_port)
            protocol = tcp
            return RuleData(protocol=protocol, from_port=from_port, to_port=to_port)

        port_match = re.match(r"^((?P<from_port>\d+))$", ports_attribute)
        # 80
        if port_match:
            port = port_match.group(from_port)
            protocol = tcp
            return RuleData(protocol=protocol, port=port)

        raise ValueError("The value '{0}' is not a valid ports rule".format(ports_attribute))
