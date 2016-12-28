class ValidatorProvider:
    def __init__(self, validators_list=[]):
        """
        :param list validators_list:
        """
        self.validators_list = validators_list

    def try_validate(self, resource_type, resource):
        """
        This method a resource and its type , finds a validator for it and validates.
        In case of an error it will throw an error based on the description of the validator
        :param resource_type:
        :param resource:
        :return:
        """
        validator = next(
            validator for validator in self.validators_list if validator.can_handle(resource_type=resource_type))
        if validator is None:
            raise Exception("Could find validation for {}".format(resource))
        return validator.validate(resource)

    def add_validator(self, validator):
        """
        Gets a validator and registers it to the list of validators
        :param validator:
        :return:
        """
        self.validators_list.append(validator)

    def add_validator_list(self, validators_list):
        """
        Gets a validator list and registers it to the list of validators
        :param [] validators_list:

        :return:
        """
        self.validators_list.append(validators_list)
