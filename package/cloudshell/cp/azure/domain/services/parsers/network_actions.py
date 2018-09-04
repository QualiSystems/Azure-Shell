import jsonpickle

from cloudshell.cp.azure.domain.services.parsers.connection_params import ConnectionParamsParser
from cloudshell.cp.azure.models.network_actions_models import NetworkAction, NetworkActionAttribute


class NetworkActionsParser(object):
    def __init__(self):
        pass

    @staticmethod
    def parse_network_actions_data(actions_data, logger):
        """
        :param [dict] actions_data:
        :rtype list[NetworkAction]
        """
        if not isinstance(actions_data, list):
            return None

        parsed_data = []
        for action in actions_data:
            network_action = NetworkAction()
            network_action.id = action.actionId
            network_action.connection_params = ConnectionParamsParser.parse(action.actionParams)
            parsed_data.append(network_action)
            logger.warn('adding action ' + action.actionId + network_action.connection_params.subnet_id)

        return parsed_data if(len(parsed_data) > 0) else None

