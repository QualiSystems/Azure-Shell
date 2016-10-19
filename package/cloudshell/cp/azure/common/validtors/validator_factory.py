class ValidatorFactory:
    def __init__(self, validators_list):
        """
        :param [Validator] validators_list:
        """
        self.validators_list = validators_list

    def try_validate(self, resource_type,resource):
        validator = next(validator for validator in self.validators_list if validator.can_handle(resource_type=resource_type))
        if validator is None:
            raise Exception("Could find validation for {}".format(resource))
        return validator.validate(resource=resource)