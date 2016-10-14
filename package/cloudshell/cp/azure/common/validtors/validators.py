# Validators
class Validator(object):
    def __init__(self, rules_list):
        """

        :param [ValidationRule] rules_list:
        """
        self.rules_list = rules_list

    def can_handle(self, resource):
        pass

    def validate(self, resource):
        failed_rules = []
        for rule in self.rules_list:
            if not rule.validate_rule(resource=resource):
                failed_rules.append(rule)

        if failed_rules:
            err_msg = ""
            for failed_rule in failed_rules:
                err_msg += " failed validating " + failed_rule.description + "rule name:" + failed_rule.name + "\n"
            raise Exception("Valiation error "+err_msg)


class SubnetValidator(Validator):
    def can_handle(self, resource):
        pass


class StorageValidator(Validator):
    def can_handle(self, resource):
        pass


# Rules
class ValidationRule(object):
    def __init__(self, rule_name, decription):
        self.rule_name = rule_name
        self.decription = decription

    def validate_rule(self, resource):
        return False


# Creation
class ValidatorFactory:
    def __init__(self, validators_list):
        """
        :param [Validator] validators_list:
        """
        self.validators_list = validators_list

    def try_validate(self, resource):
        validator = next(validator for validator in self.validators_list if validator.can_handle(resource=resource))
        if validator is None:
            raise Exception("Could find validation for {}".format(resource))
        return validator.validate(resource=resource)
