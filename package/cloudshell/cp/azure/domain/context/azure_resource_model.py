from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel


class AzureResourceModelContext(object):
    def __init__(self, context, model_parser):
        """
        Initializes an instance of AzureResourceModelContext
        :param ResourceCommandContext context: Command context
        :param AzureModelsParser model_parser:
        """
        self.context = context
        self.model_parser = model_parser

    def __enter__(self):
        """
        Initializes AzureCloudProviderResourceModel instance from a context
        :rtype: cloudshell.cp.azure.models.azure_cloud_provider_resource_model.AzureCloudProviderResourceModel
        :return :
        """
        return self.model_parser.convert_to_cloud_provider_resource_model(self.context.resource)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called upon end of the context. Does nothing
        :param exc_type: Exception type
        :param exc_val: Exception value
        :param exc_tb: Exception traceback
        :return:
        """
        pass
