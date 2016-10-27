from threading import Lock

from azure.mgmt.network.models import NetworkSecurityGroup
from azure.mgmt.network.models import SecurityRule


class SecurityGroupService(object):
    RULE_DEFAULT_PRIORITY = 1000
    RULE_PRIORITY_INCREASE_STEP = 5

    def __init__(self):
        self._lock = Lock()

    def _rule_priority_generator(self, last_priority=None):
        """Endless priority generator for NSG rules"""
        if last_priority is None:
            start_priority = self.RULE_DEFAULT_PRIORITY
        else:
            start_priority = last_priority + self.RULE_PRIORITY_INCREASE_STEP

        while True:
            yield start_priority
            start_priority += self.RULE_PRIORITY_INCREASE_STEP

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

    def _prepare_security_group_rule(self, rule_data, private_vm_ip, priority):
        """Convert inbound rule data into appropriate Azure client model

        :param rule_data: cloudshell.cp.azure.models.rule_data.RuleData instance
        :param private_vm_ip: Priavate IP of the deployed VM
        :return: azure.mgmt.network.models.SecurityRule instance
        """
        if rule_data.port:
            port_range = str(rule_data.port)
        else:
            port_range = "{}-{}".format(rule_data.from_port, rule_data.to_port)

        return SecurityRule(
            access="Allow",
            direction="Inbound",
            source_address_prefix="*",
            source_port_range="*",
            name="rule_{}".format(priority),
            destination_address_prefix=private_vm_ip,
            destination_port_range=port_range,
            priority=priority,
            protocol=rule_data.protocol)

    def create_network_security_group_rules(self, network_client, group_name, security_group_name,
                                            inbound_rules, private_vm_ip):
        """Create NSG inbound rules on the Azure

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: NSG name from the Azure
        :param inbound_rules: list[cloudshell.cp.azure.models.rule_data.RuleData]
        :param private_vm_ip: Private IP address from the Azure VM
        :return: None
        """
        with self._lock:

            security_rules = network_client.security_rules.list(resource_group_name=group_name,
                                                                network_security_group_name=security_group_name)

            security_rules = list(security_rules)

            if security_rules:
                last_rule = max(security_rules, key=lambda x: x.priority)
                last_priority = last_rule.priority
            else:
                last_priority = None

            priority_generator = self._rule_priority_generator(last_priority)

            for rule_data in inbound_rules:
                rule = self._prepare_security_group_rule(rule_data=rule_data,
                                                         private_vm_ip=private_vm_ip,
                                                         priority=next(priority_generator))

                operation_poller = network_client.security_rules.create_or_update(
                    resource_group_name=group_name,
                    network_security_group_name=security_group_name,
                    security_rule_name=rule.name,
                    security_rule_parameters=rule)

                operation_poller.wait()
