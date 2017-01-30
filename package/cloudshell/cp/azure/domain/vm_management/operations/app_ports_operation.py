from cloudshell.cp.azure.common.parsers.rules_attribute_parser import RulesAttributeParser


class DeployedAppPortsOperation(object):
    def __init__(self, vm_custom_params_extractor):
        """
        :param vm_custom_params_extractor: VmCustomParamsExtractor instance
        :return:
        """
        self.vm_custom_params_extractor = vm_custom_params_extractor

    def get_formated_deployed_app_ports(self, custom_params):
        """Get deployed application ports in nicely formatted manner

        :param custom_params: list[DeployDataHolder] array of VMCustomParams from the deployed app json
        :return: (str) deployed application ports in nicely formatted manner
        """
        inbound_ports_value = self.vm_custom_params_extractor.get_custom_param_value(custom_params, "inbound_ports")

        if not inbound_ports_value:
            return "No ports are open for inbound traffic outside of the Sandbox"

        result_str_list = []

        if inbound_ports_value:
            inbound_ports = RulesAttributeParser.parse_port_group_attribute(inbound_ports_value)
            if inbound_ports:
                result_str_list.append("Inbound ports:")
                for rule in inbound_ports:
                    result_str_list.append(self._port_rule_to_string(rule))
                result_str_list.append('')

        return '\n'.join(result_str_list)

    def _port_rule_to_string(self, port_rule):
        """Convert RuleData into a  nicely formatted string

        :param port_rule: cloudshell.cp.azure.models.rule_data.RuleData instance
        :return: (str) port rule in nicely formatted manner
        """
        if port_rule.port:
            port_str = port_rule.port
            port_postfix = ""
        else:
            port_str = "{0}-{1}".format(port_rule.from_port, port_rule.to_port)
            port_postfix = "s"

        return "Port{0} {1} {2}".format(port_postfix, port_str, port_rule.protocol)
