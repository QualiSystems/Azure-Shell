from cloudshell.cp.core.models import ConnectSubnet, ConnectToSubnetParams, PrepareSubnetParams, PrepareCloudInfra

from cloudshell.cp.azure.models.network_actions_models import *


class ConnectionParamsParser(object):
    def __init__(self):
        pass

    @staticmethod
    def parse(params_data):
        """
        :param dict params_data:
        :rtype: ConnectionParamsBase
        """
        params = None
        if not params_data:
            return params
        if isinstance(params_data, ConnectToSubnetParams):
            params = SubnetConnectionParams()
            params.subnet_id = params_data.subnetId

        elif isinstance(params_data, PrepareSubnetParams):
            params = PrepareSubnetParamsData()
            params.is_public = convert_to_bool(params_data.isPublic)
            params.alias = params_data.alias

        elif isinstance(params_data, PrepareCloudInfra):
            params = PrepareNetworkParams()

        else:
            raise ValueError("Unsupported connection params type {0}".format(type))

        ConnectionParamsParser.parse_base_data(params, params_data)

        return params

    @staticmethod
    def parse_base_data(params_base, data):
        """
        :param ConnectionParamsBase params_base:
        :param RequestObjectBase data:
        :return:
        """
        params_base.cidr = data.cidr
        params_base.subnetServiceAttributes = ConnectionParamsParser.parse_subnet_service_attributes(data)
        params_base.custom_attributes = []

    @staticmethod
    def parse_custom_network_action_attributes(action):
        """
        :param dict action:
        :rtype: [NetworkActionAttribute]
        """
        result = []
        if not isinstance(action.get("customActionAttributes"), list):
            return result

        for raw_action_attribute in action["customActionAttributes"]:
            attribute_obj = NetworkActionAttribute()
            attribute_obj.name = raw_action_attribute["attributeName"]
            attribute_obj.value = raw_action_attribute["attributeValue"]
            result.append(attribute_obj)

        return result

    @staticmethod
    def parse_subnet_service_attributes(data):
        """
        :param RequestObjectBase data:
        :rtype: [NetworkActionAttribute]
        """
        result = []

        for raw_action_attribute in data.subnetServiceAttributes:
            attribute_obj = NetworkActionAttribute()
            attribute_obj.name = raw_action_attribute
            attribute_obj.value = data.subnetServiceAttributes[raw_action_attribute]
            result.append(attribute_obj)
        return result


def convert_to_bool(string):
    """
    Converts string to bool
    :param string: String
    :str string: str
    :return: True or False
    """
    if isinstance(string, bool):
        return string
    return string in ['true', 'True', '1']
