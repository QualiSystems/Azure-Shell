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