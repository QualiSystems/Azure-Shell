import json
from logging import Logger

from azure.mgmt.network import NetworkManagementClient
from cloudshell.api.cloudshell_api import CloudShellAPISession
from netaddr import IPNetwork

from cloudshell.cp.azure.domain.services.lock_service import GenericLockProvider


class IpService(object):
    SANDBOX_LOCK_KEY = '{}-available-private-ip-key'

    def __init__(self, generic_lock_provider):
        """
        :param GenericLockProvider generic_lock_provider:
        """
        self.generic_lock_provider = generic_lock_provider
        self._cached_available_private_ips = {}

    def get_next_available_ip_from_cs_pool(self, logger, api, reservation_id, subnet_cidr, owner=None):
        """
        Call the generic pool api to checkout the next available ip
        :param Logger logger:
        :param CloudShellAPISession api:
        :param str reservation_id:
        :param str subnet_cidr:
        :return: IP address
        :rtype: str
        """

        # Build request
        request = {'type': 'NextAvailableIP',
                   'poolId': self._get_pool_id(reservation_id),
                   'reservationId': reservation_id,
                   'ownerId': self._get_pool_item_owner(owner),
                   'isolation': 'Exclusive',
                   'subnetRange': subnet_cidr,
                   'reservedIps': self._get_reserved_ips(subnet_cidr)}

        # Get next available ip from pool
        # If no ip is available api will throw an error:
        # 'CloudShell API error 100: Error occurred in CheckoutFromPool. Error: Could not find available IP.'
        result = api.CheckoutFromPool(selectionCriteriaJson=json.dumps(request))
        available_ip = result.Items[0]

        logger.info("Retrieved next available IP '{}' in subnet '{}'".format(available_ip, subnet_cidr))

        return available_ip

    def _get_pool_item_owner(self, owner):
        return 'Azure-Shell' if not owner else owner

    def _get_reserved_ips(self, subnet_cidr):
        # Calculate reserved ips by azure - The first and last IP addresses of each subnet are reserved for protocol
        # conformance, along with the x.x.x.1-x.x.x.3 addresses of each subnet, which are used for Azure services.
        ip_network = IPNetwork(subnet_cidr)
        reserved_ips = list(ip_network[0:4]) + [ip_network[-1]]
        reserved_ips_str_arr = map(lambda x: str(x), reserved_ips)
        return reserved_ips_str_arr

    def _get_pool_id(self, reservation_id):
        return '{}-private-ips'.format(reservation_id)

    def release_ips(self, logger, api, reservation_id, ips_to_release, owner=None):
        """

        :param Logger logger:
        :param CloudShellAPISession api:
        :param str reservation_id:
        :param list[str] ips_to_release:
        :return:
        """
        api.ReleaseFromPool(values=ips_to_release,
                            poolId=self._get_pool_id(reservation_id),
                            reservationId=reservation_id,
                            ownerId=self._get_pool_item_owner(owner))
        logger.info('Released ips from pool: {}'.format(','.join(ips_to_release)))