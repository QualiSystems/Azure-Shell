from cloudshell.cp.azure.common.validators import rules
from cloudshell.cp.azure.common.exceptions.validation_error import ValidationError


class AbstractDataModelValidator(object):
    @property
    def model_name(self):
        """CloudShell Data model name"""
        raise NotImplementedError("Class {} must implement property 'model_name'".format(type(self)))

    @property
    def schema(self):
        """Dictionary schema for validation"""
        raise NotImplementedError("Class {} must implement property 'schema'".format(type(self)))

    def validate(self, model_data):
        """Validate Data model attributes

        :param dict model_data: Data model attributes
        :raise: ValidationError
        """
        errors = {}
        for attr, rules in self.schema.iteritems():
            value = model_data.get(attr)
            for rule in rules:
                error = rule.validate(value, self.model_name)
                if error:
                    errors[attr] = error
                    break

        if errors:
            raise ValidationError(str(errors))


class CloudProviderDataModelValidator(AbstractDataModelValidator):
    model_name = "Microsoft Azure"

    schema = {
        "Azure Application ID": [rules.NotBlank()],
        "Azure Application Key": [rules.NotBlank()],
        "Azure Subscription ID": [rules.NotBlank()],
        "Azure Tenant ID": [rules.NotBlank()],
        "Region": [rules.NotBlank()],
        "Management Group Name": [rules.NotBlank()],
    }


class DeployAzureVMDataModelValidator(AbstractDataModelValidator):
    model_name = "Deploy Azure VM"

    schema = {
        "cloud_provider": [rules.NotBlank()],
        "image_offer": [rules.NotBlank()],
        "image_publisher": [rules.NotBlank()],
        "image_version": [rules.NotBlank()],
    }


class DeployAzureVMFromCustomImageDataModelValidator(AbstractDataModelValidator):
    model_name = "Deploy Azure VM From Custom Image"

    schema = {
        "cloud_provider": [rules.NotBlank()],
        "image_urn": [rules.NotBlank()],
        "image_os_type": [rules.NotBlank()],
    }
