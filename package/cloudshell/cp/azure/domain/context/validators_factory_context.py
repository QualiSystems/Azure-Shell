from cloudshell.cp.azure.common.validtors.validator_factory import ValidatorFactory
from cloudshell.cp.azure.common.validtors.validators import StorageValidationRuleOneVnet, StorageValidator


class ValidatorsFactoryContext(object):
    def __init__(self):
        self.validator_factory = ValidatorFactory()

        # Adding subnet validator
        storage_validation_rule_none_vnet = StorageValidationRuleOneVnet('StorageValidationRuleNoneVnet',
                                                                         'Resource Group should contain Only One Storage.')

        self.validator_factory.add_validator(StorageValidator([storage_validation_rule_none_vnet]))

    def __enter__(self):
        return self.validator_factory

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
