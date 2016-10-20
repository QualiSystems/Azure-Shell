import re

from cloudshell.cp.azure.models.rule_data import RuleData


class RulesAttributeParser(object):
    DEFAULT_PRIORITY = 1000
    PRIORITY_INCREASE_STEP = 5

    @staticmethod
    def _priority_generator(last_priority=None):
        """Endless priority generator"""
        if last_priority is None:
            start_priority = RulesAttributeParser.DEFAULT_PRIORITY
        else:
            start_priority = last_priority + RulesAttributeParser.PRIORITY_INCREASE_STEP

        while True:
            yield start_priority
            start_priority += RulesAttributeParser.PRIORITY_INCREASE_STEP

    @staticmethod
    def parse_port_group_attribute(ports_attribute, last_priority=None):
        """
        :param ports_attribute:
        :param last_priority:
        :return: list[PortData]
        """
        if ports_attribute:
            splitted_ports = ports_attribute.strip().split(';')
            priority_generator = RulesAttributeParser._priority_generator(last_priority)

            return [
                RulesAttributeParser._single_port_parse(port.strip(), next(priority_generator))
                for port in splitted_ports]

    @staticmethod
    def _single_port_parse(ports_attribute, priority):
        from_port = 'from_port'
        to_port = 'to_port'
        protocol = 'protocol'
        tcp = 'tcp'

        from_to_protocol_match = re.match(r"^((?P<from_port>\d+)-(?P<to_port>\d+):(?P<protocol>(udp|tcp)))$",
                                          ports_attribute)

        # 80-50000:udp
        if from_to_protocol_match:
            from_port = from_to_protocol_match.group(from_port)
            to_port = from_to_protocol_match.group(to_port)
            protocol = from_to_protocol_match.group(protocol)
            return RuleData(protocol=protocol, priority=priority, from_port=from_port, to_port=to_port)

        from_protocol_match = re.match(r"^((?P<from_port>\d+):(?P<protocol>(udp|tcp)))$", ports_attribute)

        # 80:udp
        if from_protocol_match:
            port = from_protocol_match.group(from_port)
            protocol = from_protocol_match.group(protocol)
            return RuleData(protocol=protocol, priority=priority, port=port)

        from_to_match = re.match(r"^((?P<from_port>\d+)-(?P<to_port>\d+))$", ports_attribute)

        # 20-80

        if from_to_match:
            from_port = from_to_match.group(from_port)
            to_port = from_to_match.group(to_port)
            protocol = tcp
            return RuleData(protocol=protocol, priority=priority, from_port=from_port, to_port=to_port)

        port_match = re.match(r"^((?P<from_port>\d+))$", ports_attribute)
        # 80
        if port_match:
            port = port_match.group(from_port)
            protocol = tcp
            return RuleData(protocol=protocol, priority=priority, port=port)

        raise ValueError("The value '{0}' is not a valid ports rule".format(ports_attribute))
