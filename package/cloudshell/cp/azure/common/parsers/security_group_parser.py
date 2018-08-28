from cloudshell.cp.azure.common.parsers.port_group_attribute_parser import PortGroupAttributeParser
from cloudshell.cp.azure.models.app_security_groups_model import SecurityGroupConfiguration


class SecurityGroupParser(object):
    def __init__(self):
        pass

    @staticmethod
    def parse_security_group_configurations(data):
        """
        :param [list] data:
        :rtype list[SecurityGroupConfiguration]
        """
        if not isinstance(data, list):
            return None

        parsed_data = []

        for configuration in data:
            sg_configuration = SecurityGroupConfiguration()
            sg_configuration.subnet_id = configuration.subnetId
            rules = configuration.rules
            sg_configuration.rules = PortGroupAttributeParser.parse_security_group_rules_to_port_data(rules)
            parsed_data.append(sg_configuration)

        return parsed_data if (len(parsed_data) > 0) else None
