import re


class AzureResourceIdParser(object):

    @staticmethod
    def get_name_from_resource_id(resource_id):
        """Get resource name from the Azure resource id

        :param str resource_id: Azure resource Id
        :return: Azure resource name
        :rtype: str
        """
        return resource_id.rstrip("/").split("/")[-1]

    @staticmethod
    def get_resource_group_name(resource_id):
        """Get resource group name from the Azure resource id

        :param str resource_id: Azure resource Id
        :return: Azure resource group name
        :rtype: str
        """
        match_groups = re.match(r".*resourcegroups/(?P<group_name>[^/]*)/.*", resource_id, flags=re.IGNORECASE)
        return match_groups.group("group_name")
