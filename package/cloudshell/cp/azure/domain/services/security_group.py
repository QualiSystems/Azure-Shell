from threading import Lock

from azure.mgmt.network.models import NetworkSecurityGroup, RouteNextHopType, SecurityRuleProtocol, SecurityRuleAccess
from azure.mgmt.network.models import SecurityRule
from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error
from cloudshell.cp.azure.models.port_data import PortData
from cloudshell.cp.azure.models.rule_data import RuleData

SANDBOX_NSG_NAME = "NSG_sandbox_all_subnets_"

class SecurityGroupService(object):
    RULE_DEFAULT_PRIORITY = 1000
    RULE_PRIORITY_INCREASE_STEP = 5

    def __init__(self, network_service):
        self.network_service = network_service

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

        relevant_existing_priorities = [ep for ep in existing_priorities if ep >= start_limit]
        relevant_existing_priorities = sorted(relevant_existing_priorities)

        i = 0
        while True:
            priority = relevant_existing_priorities[i] + self.RULE_PRIORITY_INCREASE_STEP
            if relevant_existing_priorities[i + 1] > priority:
                relevant_existing_priorities.insert(i + 1, priority)
                yield priority

            i += 1

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def list_network_security_group(self, network_client, group_name):
        """Get all NSG from the Azure for given resource group

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :return: list of azure.mgmt.network.models.NetworkSecurityGroup instances
        """
        return list(network_client.network_security_groups.list(group_name))

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
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

    def _prepare_security_group_rule(self, rule_data, destination_address, priority, access="Allow",
                                     source_address=RouteNextHopType.internet):
        """Convert inbound rule data into appropriate Azure client model

        :type source_address: RouteNextHopType
        :param rule_data: cloudshell.cp.azure.models.rule_data.RuleData instance
        :param destination_address: Destination IP address/CIDR
        :return: azure.mgmt.network.models.SecurityRule instance
        """
        rule_name = "rule_{}".format(priority)

        if isinstance(rule_data, RuleData):
            if rule_data.port:
                port_range = str(rule_data.port)
            else:
                port_range = "{}-{}".format(rule_data.from_port, rule_data.to_port)

            access = rule_data.access

        elif isinstance(rule_data, PortData):
            source_address = rule_data.source
            if rule_data.from_port == rule_data.to_port:
                port_range = str(rule_data.from_port)
            else:
                port_range = "{}-{}".format(rule_data.from_port, rule_data.to_port)

        else:
            raise ValueError("Unsupported type")

        if rule_data.name:
            rule_name = rule_data.name

        return SecurityRule(
            access=access,
            direction="Inbound",
            source_address_prefix=source_address,
            source_port_range=SecurityRuleProtocol.asterisk,
            name=rule_name,
            destination_address_prefix=destination_address,
            destination_port_range=port_range,
            priority=priority,
            protocol=rule_data.protocol)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_network_security_group_rule(self, network_client, group_name, security_group_name, rule_data,
                                           destination_addr, priority,
                                           source_address=RouteNextHopType.internet):
        """Create NSG inbound rule on the Azure

        :param source_address: RouteNextHopType
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: NSG name from the Azure
        :param rule_data: cloudshell.cp.azure.models.rule_data.RuleData instance
        :param destination_addr: Destination IP address/CIDR
        :param priority: (int) rule priority number
        :return: azure.mgmt.network.models.SecurityRule instance
        """
        rule = self._prepare_security_group_rule(rule_data=rule_data,
                                                 destination_address=destination_addr,
                                                 priority=priority,
                                                 source_address=source_address)

        operation_poller = network_client.security_rules.create_or_update(
            resource_group_name=group_name,
            network_security_group_name=security_group_name,
            security_rule_name=rule.name,
            security_rule_parameters=rule)

        return operation_poller.result()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_network_security_group_custom_rule(self, network_client, group_name, security_group_name, rule,
                                                  async=False):
        """Create NSG inbound management rule on the Azure

        :param rule: azure.mgmt.network.models.security_rule.SecurityRule
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: NSG name from the Azure
        :param rule: azure.mgmt.network.models.SecurityRule instance
        :param async: (bool) wait/no for result operation
        :return: azure.mgmt.network.models.SecurityRule/msrestazure.azure_operation.AzureOperationPoller
        """
        operation_poller = network_client.security_rules.create_or_update(
            resource_group_name=group_name,
            network_security_group_name=security_group_name,
            security_rule_name=rule.name,
            security_rule_parameters=rule)

        if async:
            return operation_poller

        return operation_poller.result()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_first_network_security_group(self, network_client, group_name):
        network_security_groups = self.list_network_security_group(
            network_client=network_client,
            group_name=group_name)
        if len(network_security_groups) == 0:
            raise Exception("The resource group {} does not contain a network security group.".format(group_name))
        return network_security_groups[0]

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def get_network_security_group(self, network_client, group_name, nsg_name):
        nsg = network_client.network_security_groups.get(resource_group_name=group_name,
                                                         network_security_group_name=nsg_name)

        return nsg

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_network_security_group_rules(self, network_client, group_name, security_group_name,
                                            inbound_rules, destination_addr, lock, start_from=None,
                                            source_address=RouteNextHopType.internet):
        """Create NSG inbound rules on the Azure

        :param source_address: RouteNextHopType
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: NSG name from the Azure
        :param inbound_rules: list[cloudshell.cp.azure.models.rule_data.RuleData]
        :param destination_addr: Destination IP address/CIDR
        :param threading.Lock lock: The locker object to use to sync between concurrent operations on the NSG
        :param start_from: (int) rule priority number to start from
        :return: None
        """
        with lock:
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
                    priority=next(priority_generator),
                    source_address=source_address)

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def create_isolated_network_security_group_rules(self, network_client, group_name, security_group_name, lock):
        """Create NSG inbound rules on the Azure

        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param group_name: resource group name (reservation id)
        :param security_group_name: NSG name from the Azure
        :param inbound_rules: list[cloudshell.cp.azure.models.rule_data.RuleData]
        :param destination_addr: Destination IP address/CIDR
        :param threading.Lock lock: The locker object to use to sync between concurrent operations on the NSG
        :param start_from: (int) rule priority number to start from
        :return: None
        """
        with lock:
            # 1. add rule to allow azure load balancer inbound traffic. It is needed in order to avoid core
            # azure services interruption
            allow_azure_lb = SecurityRule(access=SecurityRuleAccess.allow,
                                          direction='Inbound',
                                          source_address_prefix='AzureLoadBalancer',
                                          source_port_range='*',
                                          name='allow_azure_lb',
                                          destination_address_prefix='*',
                                          destination_port_range='*',
                                          priority=4010,
                                          protocol='*')

            operation_poller = network_client.security_rules.create_or_update(
                resource_group_name=group_name,
                network_security_group_name=security_group_name,
                security_rule_name=allow_azure_lb.name,
                security_rule_parameters=allow_azure_lb)

            operation_poller.result()

            # 2. deny all inbound traffic (with higher priority than 'allow_azure_lb' rule
            deny_all_in = SecurityRule(access=SecurityRuleAccess.deny,
                                       direction='Inbound',
                                       source_address_prefix='*',
                                       source_port_range='*',
                                       name='deny_all_in',
                                       destination_address_prefix='*',
                                       destination_port_range='*',
                                       priority=4020,
                                       protocol='*')

            operation_poller = network_client.security_rules.create_or_update(
                resource_group_name=group_name,
                network_security_group_name=security_group_name,
                security_rule_name=deny_all_in.name,
                security_rule_parameters=deny_all_in)

            operation_poller.result()

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_custom_security_rules_from_nsg(self, network_client, resource_group_name, network_security_group_name,
                                              lock, logger):
        """
        removes NSG custom rules from NSG. Custom rules are simply rules whose name begins with custom_rule

        :param network_security_group_name:
        :param logger:
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param resource_group_name: resource group name (reservation id)
        :param threading.Lock lock: The locker object to use to sync between concurrent operations on the NSG

        :return: None
        """

        logger.info('Preparing to delete custom security rules in {0}'.format(network_security_group_name))

        rules_in_nsg = list(network_client.security_rules.list(resource_group_name, network_security_group_name))
        custom_rules = [r for r in rules_in_nsg if 'custom_rule' in r.name]

        with lock:
            for rule in custom_rules:
                result = network_client.security_rules.delete(resource_group_name,
                                                              network_security_group_name,
                                                              rule.name)
                logger.info("Deleting custom security rule: {0} in {1}".format(rule.name, network_security_group_name))
                result.wait()
                logger.info("Deleted custom security rule: {0} in {1}".format(rule.name, network_security_group_name))

        logger.info('Finished deleting custom security rules in {0}'.format(network_security_group_name))

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def delete_security_rules(self, network_client, resource_group_name, vm_name, lock, logger):
        """
        removes NSG inbound rules for virtual machine (based on private ip address)

        :param logger:
        :param vm_name:
        :param network_client: azure.mgmt.network.NetworkManagementClient instance
        :param resource_group_name: resource group name (reservation id)
        :param threading.Lock lock: The locker object to use to sync between concurrent operations on the NSG

        :return: None
        """

        private_ip_address = self.network_service.get_private_ip(network_client=network_client,
                                                                 group_name=resource_group_name,
                                                                 vm_name=vm_name)
        # todo - change to get the correct NSG
        security_group = self.get_first_network_security_group(network_client=network_client,
                                                               group_name=resource_group_name)

        if security_group is None:
            raise Exception("Could not find NetworkSecurityGroup in '{}'".format(resource_group_name))

        rules = security_group.security_rules

        vm_rules = [rule for rule in rules if rule.destination_address_prefix == private_ip_address]

        if vm_rules is None or len(vm_rules) == 0:
            return

        with lock:
            for vm_rule in vm_rules:
                logger.info("Deleting security group rule '{}'.".format(vm_rule.name))
                result = network_client.security_rules.delete(
                    resource_group_name=resource_group_name,
                    network_security_group_name=security_group.name,
                    security_rule_name=vm_rule.name)
                result.wait()
                logger.info("Security group rule '{}' deleted.".format(vm_rule.name))

    def get_subnets_nsg_name(self, reservation_id):
        return SANDBOX_NSG_NAME + reservation_id
