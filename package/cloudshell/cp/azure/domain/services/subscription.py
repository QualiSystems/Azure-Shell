from retrying import retry

from cloudshell.cp.azure.common.helpers.retrying_helpers import retry_if_connection_error


class SubscriptionService(object):

    @retry(stop_max_attempt_number=5, wait_fixed=2000, retry_on_exception=retry_if_connection_error)
    def list_available_regions(self, subscription_client, subscription_id):
        """List all available regions per subscription

        :param subscription_client:
        :param subscription_id:
        :rtype: list[azure.mgmt.resource.subscriptions.models.Location]
        """
        locations = subscription_client.subscriptions.list_locations(subscription_id)
        return list(locations)
