class AbstractRule(object):
    def is_valid(self, value):
        """Check if value is valid or not

        :param value: value to validate
        :return: True/False whether value is valid or not
        :rtype: bool
        """
        raise NotImplementedError("Class {} must implement method 'is_valid'".format(type(self)))

    def format_message(self, value, model_name):
        """Format error message

        :param value: value to validate
        :param str model_name: CloudShell Data model name
        :return: error message
        :rtype: str
        """
        raise NotImplementedError("Class {} must implement method 'format_message'".format(type(self)))

    def validate(self, value, model_name):
        """Validate given value, return error message if it is not valid

        :param value: value to validate
        :param str model_name: CloudShell Data model name
        :return:
        """
        if not self.is_valid(value):
            return self.format_message(value, model_name)


class NotBlank(AbstractRule):

    def is_valid(self, value):
        return value != ""

    def format_message(self, value, model_name):
        return "Attribute can't be empty on {} model".format(model_name)
