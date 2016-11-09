from threading import Lock

from azure.mgmt.network.models import NetworkSecurityGroup
from azure.mgmt.network.models import SecurityRule


class SecurityGroupService(object):
    RULE_DEFAULT_PRIORITY = 1000
    RULE_PRIORITY_INCREASE_STEP = 5

    def __init__(self):
        self._lock = Lock()

    def _rule_priority_generator(self, existing_rules, start_from=None):
        """Endless priority generator for NSG rules

        :param existing_rules: list[azure.mgmt.network.models.SecurityRule] instances
        :param start_from: (int) rule priority number to start from
        :return: priority generator => (int) next available priority
        """
        if start_from is None:
            start_from = self.RULE_DEFAULT_PRIORITY

        existing_priorities = [rule.priority for rule in existing_rules]
        start_limit = start_from - self.RULE_PRIORITY_INCREASE_STEP
        end_limit = float("inf")
        existing_priorities.extend([start_limit, end_limit])
        existing_priorities = sorted(existing_priorities)

        i = 0
        while True:
            priority = existing_priorities[i] + self.RULE_PRIORITY_INCREASE_STEP
            if priority < existing_priorities[i + 1]:
                existing_priorities.insert(i + 1, priority)
                yield priority

            i += 1

    def list_network_security_group(self, network_client, group_name):
        """Get all NSG from the Azure for given resource group

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :return: list of azure.mgmt.network.models.NetworkSecurityGroup instances
        """
        return list(network_client.network_security_groups.list(group_name))

    def create_network_security_group(self, network_client, group_name, security_group_name, region, tags=None):
        """Create NSG on the Azure

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: name for NSG on Azure
        :param region: Azure location
        :param tags: tags
        :return: azure.mgmt.network.models.NetworkSecurityGroup instance
        """
        nsg_model = NetworkSecurityGroup(location=region, tags=tags)
        operation_poler = network_client.network_security_groups.create_or_update(
            resource_group_name=group_name,
            network_security_group_name=security_group_name,
            parameters=nsg_model)

        return operation_poler.result()

    def _prepare_security_group_rule(self, rule_data, destination_addr, priority, access="Allow"):
        """Convert inbound rule data into appropriate Azure client model

        :param rule_data: cloudshell.cp.azure.models.rule_data.RuleData instance
        :param destination_addr: Destination IP address/CIDR
        :return: azure.mgmt.network.models.SecurityRule instance
        """
        if rule_data.port:
            port_range = str(rule_data.port)
        else:
            port_range = "{}-{}".format(rule_data.from_port, rule_data.to_port)

        return SecurityRule(
            access=access,
            direction="Inbound",
            source_address_prefix="*",
            source_port_range="*",
            name="rule_{}".format(priority),
            destination_address_prefix=destination_addr,
            destination_port_range=port_range,
            priority=priority,
            protocol=rule_data.protocol)

    def create_network_security_group_rule(self, network_client, group_name, security_group_name, rule_data,
                                           destination_addr, priority, access="Allow"):
        """Create NSG inbound rule on the Azure

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: NSG name from the Azure
        :param rule_data: cloudshell.cp.azure.models.rule_data.RuleData instance
        :param destination_addr: Destination IP address/CIDR
        :param priority: (int) rule priority number
        :return: azure.mgmt.network.models.SecurityRule instance
        """
        rule = self._prepare_security_group_rule(rule_data=rule_data,
                                                 destination_addr=destination_addr,
                                                 priority=priority)

        operation_poller = network_client.security_rules.create_or_update(
            resource_group_name=group_name,
            network_security_group_name=security_group_name,
            security_rule_name=rule.name,
            security_rule_parameters=rule)

        return operation_poller.result()

    def create_network_security_group_custom_rule(self, network_client, group_name, security_group_name, rule):
        """Create NSG inbound rule on the Azure

        :param rule: azure.mgmt.network.models.security_rule.SecurityRule
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: NSG name from the Azure
        :param rule_data: cloudshell.cp.azure.models.rule_data.RuleData instance
        :param destination_addr: Destination IP address/CIDR
        :param priority: (int) rule priority number
        :return: azure.mgmt.network.models.SecurityRule instance
        """
        with self._lock:
            security_rules = network_client.security_rules.list(resource_group_name=group_name,
                                                                network_security_group_name=security_group_name)
            security_rules = list(security_rules)
            priority = self._rule_priority_generator(existing_rules=security_rules, start_from=rule.priority)
            rule.priority = next(priority)

            operation_poller = network_client.security_rules.create_or_update(
                resource_group_name=group_name,
                network_security_group_name=security_group_name,
                security_rule_name=rule.name,
                security_rule_parameters=rule)

            return operation_poller.result()

    def create_network_security_group_rules(self, network_client, group_name, security_group_name,
                                            inbound_rules, destination_addr, start_from=None):
        """Create NSG inbound rules on the Azure

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: NSG name from the Azure
        :param inbound_rules: list[cloudshell.cp.azure.models.rule_data.RuleData]
        :param destination_addr: Destination IP address/CIDR
        :param start_from: (int) rule priority number to start from
        :return: None
        """
        with self._lock:
            security_rules = network_client.security_rules.list(resource_group_name=group_name,
                                                                network_security_group_name=security_group_name)
            security_rules = list(security_rules)
            priority_generator = self._rule_priority_generator(existing_rules=security_rules, start_from=start_from)

            for rule_data in inbound_rules:
                self.create_network_security_group_rule(
                    network_client=network_client,
                    group_name=group_name,
                    security_group_name=security_group_name,
                    rule_data=rule_data,
                    destination_addr=destination_addr,
                    priority=next(priority_generator))
