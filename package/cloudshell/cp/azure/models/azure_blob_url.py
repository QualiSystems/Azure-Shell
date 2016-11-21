class AzureBlobUrlModel(object):

    def __init__(self, storage_name, container_name, blob_name):
        """
        :param storage_name: (str) Azure storage name
        :param container_name: (str) Azure container name
        :param blob_name: (str) Azure Blob name
        """
        self.storage_name = storage_name
        self.container_name = container_name
        self.blob_name = blob_name
