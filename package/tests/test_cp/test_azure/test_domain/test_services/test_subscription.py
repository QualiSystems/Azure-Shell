from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.services.subscription import SubscriptionService


class TestSubscriptionService(TestCase):
    def setUp(self):
        self.subscription_service = SubscriptionService()

    def test_list_available_regions(self):
        """Check that method will use subscription client to get list of available regions"""
        subscription_client = mock.MagicMock()
        subscription_id = "subscription ID"

        result = self.subscription_service.list_available_regions(subscription_client=subscription_client,
                                                                  subscription_id=subscription_id)

        self.assertIsInstance(result, list)
        subscription_client.subscriptions.list_locations.assert_called_once_with(subscription_id)
