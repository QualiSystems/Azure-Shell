from threading import Lock

from azure.mgmt.network.models import NetworkSecurityGroup
from azure.mgmt.network.models import SecurityRule


class SecurityGroupService(object):

    def __init__(self):
        self._lock = Lock()

    def list_network_security_group(self, network_client, group_name):
        """Get all NSG from the Azure for given resource group

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resourse group name (reservation id)
        :return:
        """
        return list(network_client.network_security_groups.list(group_name))

    def create_network_security_group(self, network_client, group_name, security_group_name, region, tags=None):
        """Create NSG on the Azure

        :param network_client:
        :param group_name:
        :param security_group_name:
        :param region:
        :param tags:
        :return:
        """
        nsg_model = NetworkSecurityGroup(location=region, tags=tags)
        operation_poler = network_client.network_security_groups.create_or_update(
            resource_group_name=group_name,
            network_security_group_name=security_group_name,
            parameters=nsg_model)

        return operation_poler.result()

    def _prepare_security_group_rule(self, rule_data, private_vm_ip):
        """

        :param rule_data:
        :param private_vm_ip:
        :return:
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
            name="rule_{}".format(rule_data.priority),
            destination_address_prefix=private_vm_ip,
            destination_port_range=port_range,
            priority=rule_data.priority,
            protocol=rule_data.protocol)

    def create_network_security_group_rules(self, network_client, group_name, security_group_name,
                                            inbound_rules, private_vm_ip):
        """

        :param network_client:
        :param group_name:
        :param security_group_name:
        :param inbound_rules:
        :param private_vm_ip:
        :return:
        """
        with self._lock:
            for rule_data in inbound_rules:
                rule = self._prepare_security_group_rule(rule_data, private_vm_ip)

                operation_poller = network_client.security_rules.create_or_update(
                    resource_group_name=group_name,
                    network_security_group_name=security_group_name,
                    security_rule_name=rule.name,
                    security_rule_parameters=rule)

                operation_poller.wait()
