from cloudshell.cp.azure.common.validtors.provider import ValidatorProvider
from cloudshell.cp.azure.common.validtors.validators import StorageValidationRuleOneVnet, StorageValidator


class ValidatorFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def get_validator():
        validator = ValidatorProvider()

        # Adding storage validator
        storage_validation_rule_none_vnet = StorageValidationRuleOneVnet('StorageValidationRuleNoneVnet',
                                                                         'Resource Group should contain Only One Storage')

        validator.add_validator(StorageValidator([storage_validation_rule_none_vnet]))

        return validator
