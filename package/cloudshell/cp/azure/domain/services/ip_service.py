from threading import Lock


class IpService(object):
    def __init__(self):
        self._cached_available_private_ips = {}
        self._available_private_ips_lock = Lock()

    def get_available_private_ip(self, network_client, group_name, virtual_network_name, ip_address, logger):
        """
        The method returns the checked ip_address if this available or the next available ip
        :param network_client:
        :param group_name:
        :param virtual_network_name: network in the group name
        :param ip_address: ip address checked for availability
        :param logger:
        :return:
        """

        cached_key = (group_name, virtual_network_name, ip_address)

        if not self._cached_available_private_ips.get(cached_key):
            with self._available_private_ips_lock:
                if not self._cached_available_private_ips.get(cached_key):
                    availability = network_client.virtual_networks.check_ip_address_availability(
                        group_name,
                        virtual_network_name,
                        ip_address
                    )

                    logger.info(
                        "Retrieving available IP for {} in {}, checking {}".format(virtual_network_name,
                                                                                   group_name, ip_address))

                    if availability.available:
                        return ip_address
                    else:
                        self._cached_available_private_ips[cached_key] = availability.available_ip_addresses

        if ip_address in self._cached_available_private_ips[cached_key]:
            self._cached_available_private_ips[cached_key].remove(ip_address)
            available_ip = ip_address
        else:
            available_ip = self._cached_available_private_ips[cached_key].pop(0)

        return available_ip
