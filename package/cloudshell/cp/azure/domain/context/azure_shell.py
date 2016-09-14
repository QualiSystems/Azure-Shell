#
# class AzureShellContext(object):
#     def __init__(self, context):
#         self.context = context
#         self.model_parser = AzureModelsParser()
#
#     def __enter__(self):
#         """
#         Initializes all azure shell context dependencies
#         :rtype AzureShellContextModel:
#         """
#         with LoggingSessionContext(self.context) as logger:
#             with ErrorHandlingContext(logger):
#                 with AzureResourceModelContext(self.context, self.model_parser) as azure_resource_model:
#                     # todo use azure_resource_model for ComputeManagementClientContext and other
#                     return AzureShellContextModel(logger=logger)
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """
#         Called upon end of the context. Does nothing
#         :param exc_type: Exception type
#         :param exc_val: Exception value
#         :param exc_tb: Exception traceback
#         :return:
#         """
#         pass
#
#
# class AzureShellContextModel(object):
#     def __init__(self, logger):
#         """
#         :param logging.Logger logger:
#         :return:
#         """
#         self.logger = logger
#         self.compute_client = ComputeManagementClient(
#             "TBD",
#             "TBD")
