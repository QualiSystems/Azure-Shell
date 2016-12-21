from unittest import TestCase

import time

from cloudshell.cp.azure.common.azure_clients import AzureClientsManager
from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel


class TestIp(TestCase):
    def setUp(self):
        self.model = AzureCloudProviderResourceModel()
        self.model.azure_client_id = '3d8aeb15-9d91-4e79-b0c8-cef0d7f495f8'  # type: str
        self.model.azure_mgmt_network_d = ''  # type: str
        self.model.azure_mgmt_nsg_id = ''  # type: str
        self.model.azure_secret = 'ZSAG4NOHUgIM7+fBb+Zj7+0McfX4HiFgueGEeO40pa0='  # type: str
        self.model.region = 'westeurope'  # type: str
        self.model.instance_type = ''  # type: str
        self.model.keypairs_location = ''  # type: str
        self.model.networks_in_use = '10.0.0.0/24'  # type: str
        self.model.azure_subscription_id = '533d31a2-915f-44aa-9807-e2a1cb89b60e'  # type: str
        self.model.azure_tenant = '0edc0c17-b88c-45b9-a974-46e0eec3684d'  # type: str
        self.model.storage_type = 'Basic_A0'  # type: str
        self.model.management_group_name = 'MgntIgor'  # type: str
        self.azure_clients = AzureClientsManager(self.model)

    def test_ip_address_availability(self):
        availability = self.azure_clients.network_client.virtual_networks.check_ip_address_availability(
            "MgntIgor",
            "SandboxVNET",
            "10.0.1.0"
        )
        print(availability.available)
        print(availability.available_ip_addresses)

    def test_ip_address_availability_performance(self):
        start_time = time.time()

        for x in range(0, 255):
            availability = self.azure_clients.network_client.virtual_networks.check_ip_address_availability(
                "MgntIgor",
                "SandboxVNET",
                "10.0.1." + str(x)
            )
            print(availability.available)
            print(availability.available_ip_addresses)

        elapsed_time = time.time() - start_time
        print(elapsed_time)

