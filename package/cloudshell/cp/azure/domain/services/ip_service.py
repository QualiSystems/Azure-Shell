from threading import Lock


class IpService(object):
    def __init__(self):
        self._cached_available_private_ips = {}
        self._available_private_ips_lock = Lock()

    def get_available_private_ip(self, network_client, management_group_name, virtual_network_name, ip_address, logger):
        cached_key = (management_group_name, virtual_network_name, ip_address)

        with self._available_private_ips_lock:
            available_private_ips = self._cached_available_private_ips.get(cached_key)
            if not available_private_ips:
                availability = network_client.virtual_networks.check_ip_address_availability(
                    management_group_name,
                    virtual_network_name,
                    ip_address
                )

                available_private_ips = availability.available_ip_addresses

                self._cached_available_private_ips[cached_key] = available_private_ips

                logger.info(
                    "Retrieving available IPs for {} in {}".format(virtual_network_name, management_group_name))

            available_ip = self._cached_available_private_ips[cached_key].pop(0)

        return available_ip
