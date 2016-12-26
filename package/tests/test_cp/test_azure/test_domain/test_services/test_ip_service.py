from unittest import TestCase

from mock import MagicMock

from cloudshell.cp.azure.domain.services.ip_service import IpService


class TestIpService(TestCase):
    def setUp(self):
        self.key_pair_service = IpService()
        self.group_name = "tested_group"
        self.virtual_network_name = "tested_network"
        self.tested_ip_address = "10.0.1.1"
        self.cached_key = (self.group_name, self.virtual_network_name, self.tested_ip_address)
        self.logger = MagicMock()
        self.network_client = MagicMock()

    def test_no_calls_if_cache_exists(self):
        # Arrange
        self.key_pair_service._cached_available_private_ips[self.cached_key] = [self.tested_ip_address]

        # Act
        self.key_pair_service.get_available_private_ip(self.network_client, self.group_name, self.virtual_network_name,
                                                       self.tested_ip_address, self.logger)

        # Verify
        self.network_client.virtual_networks.check_ip_address_availability.assert_not_called()

    def test_check_ip_address_availability_called(self):
        # Arrange
        self.key_pair_service._cached_available_private_ips = {}

        # Act
        self.key_pair_service.get_available_private_ip(self.network_client, self.group_name, self.virtual_network_name,
                                                       self.tested_ip_address, self.logger)

        # Verify
        self.network_client.virtual_networks.check_ip_address_availability.assert_called_once_with(
            self.group_name, self.virtual_network_name, self.tested_ip_address
        )
