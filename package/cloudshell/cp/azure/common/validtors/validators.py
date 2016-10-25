# Validators
from azure.mgmt.storage.models import StorageAccount


class ValidationRule(object):
    def __init__(self, rule_name, decription):
        self.rule_name = rule_name
        self.decription = decription

    def validate_rule(self, resource):
        return False


class Validator(object):
    def __init__(self, rules_list):
        """

        :param [ValidationRule] rules_list:
        """
        self.rules_list = rules_list

    def can_handle(self, resource_type):
        pass

    def validate(self, resource):
        failed_rules = []
        for rule in self.rules_list:
            if not rule.validate_rule(resource):
                failed_rules.append(rule)

        if failed_rules:
            err_msg = ""
            for failed_rule in failed_rules:
                err_msg += " failed validating " + failed_rule.description + "rule name:" + failed_rule.name + "\n"
            raise Exception("Validation error " + err_msg)


class NetworkValidator(Validator):
    def can_handle(self, resource_type):
        pass


class NetWorkValidationRuleOneVnet(ValidationRule):
    def validate_rule(self, network):
        return len(network) == 1


class StorageValidator(Validator):
    def can_handle(self, resource_type):
        return resource_type is StorageAccount


class StorageValidationRuleOneVnet(ValidationRule):
    def validate_rule(self, storage_accounts_list):
        return len(storage_accounts_list) == 1
