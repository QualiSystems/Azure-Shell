class AzureResourceIdParser(object):

    @staticmethod
    def get_name_from_resource_id(resource_id):
        """Get resource name from the Azure resource id

        :param resource_id: (str) Azure resource Id
        :return: (str) Azure resource name
        """
        return resource_id.rstrip("/").split("/")[-1]
