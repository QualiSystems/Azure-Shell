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

    def get_available_private_ip_from_azure(self, network_client, vnet_group_name, vnet_name, sandbox_group_name,
                                            ip_address, logger):
        """
        The method returns the checked ip_address if this available or the next available ip
        :param NetworkManagementClient network_client:
        :param str vnet_group_name:
        :param str vnet_name: virtual network in the vnet_group_name
        :param str sandbox_group_name: sandbox resource group name. Used for syncing operations on the same sandbox.
        :param str ip_address: ip address checked for availability
        :param Logger logger:
        :return:
        """

        cached_key = (vnet_group_name, vnet_name, ip_address)

        with self.generic_lock_provider.get_resource_lock(
                IpService.SANDBOX_LOCK_KEY.format(sandbox_group_name), logger):
            if not self._cached_available_private_ips.get(cached_key):
                logger.info(
                    "Retrieving available IP for {} in {}, checking {}".format(vnet_name,
                                                                               vnet_group_name, ip_address))

                availability = network_client.virtual_networks.check_ip_address_availability(
                    vnet_group_name,
                    vnet_name,
                    ip_address
                )

                if availability.available:
                    return ip_address
                else:
                    self._cached_available_private_ips[cached_key] = availability.available_ip_addresses
                    return self._checkout_available_ip(cached_key, ip_address)

            return self._checkout_available_ip(cached_key, ip_address)

    def _checkout_available_ip(self, cached_key, ip_address):
        if ip_address in self._cached_available_private_ips[cached_key]:
            self._cached_available_private_ips[cached_key].remove(ip_address)
            available_ip = ip_address
        else:
            available_ip = self._cached_available_private_ips[cached_key].pop(0)
        return available_ip

    def release_ips(self, logger, api, reservation_id, ips_to_release):
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