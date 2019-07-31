import uuid
from unittest import TestCase

from mock import MagicMock

from cloudshell.cp.azure.domain.services.ip_service import IpService


class TestIpService(TestCase):
    def setUp(self):
        lock_provider = MagicMock()
        self.key_pair_service = IpService(lock_provider)
        self.group_name = "tested_group"
        self.vnet_group_name = "management_group"
        self.virtual_network_name = "tested_network"
        self.tested_ip_address = "10.0.1.1"
        self.cached_key = (self.vnet_group_name, self.virtual_network_name, self.tested_ip_address)
        self.logger = MagicMock()
        self.network_client = MagicMock()

    def test_get_next_available_ip_from_cs_pool(self):
        api = MagicMock()
        available_ip = '10.2.2.2'
        checkout_from_pool_result = MagicMock()
        checkout_from_pool_result.Items = [available_ip]
        api.CheckoutFromPool.return_value = checkout_from_pool_result
        reservation_id = str(uuid.uuid4())
        subnet_cidr = '10.2.2.0/24'

        result = self.key_pair_service.get_next_available_ip_from_cs_pool(self.logger,
                                                                          api,
                                                                          reservation_id,
                                                                          subnet_cidr)
        self.assertEqual(available_ip, result)
