from unittest import TestCase

import mock

from cloudshell.cp.azure.common.azure_clients import AzureClientsManager


class TesAzureClientsManager(TestCase):
    def setUp(self):
        self.cloud_provider = mock.MagicMock()

        with mock.patch("cloudshell.cp.azure.common.azure_clients.ServicePrincipalCredentials"):
            self.azure_clients_manager = AzureClientsManager(cloud_provider=self.cloud_provider)

    def test_init(self):
        """Check that __init__ method sets correct params for the instance"""
        cloud_provider = mock.MagicMock()
        subscription_id = mock.MagicMock()
        application_id = mock.MagicMock()
        application_key = mock.MagicMock()
        tenant = mock.MagicMock()
        service_credentials = mock.MagicMock()

        with mock.patch.object(AzureClientsManager, "_get_subscription", return_value=subscription_id):
            with mock.patch.object(AzureClientsManager, "_get_azure_application_id", return_value=application_id):
                with mock.patch.object(AzureClientsManager, "_get_azure_application_key", return_value=application_key):
                    with mock.patch.object(AzureClientsManager, "_get_azure_tenant", return_value=tenant):
                        with mock.patch.object(AzureClientsManager, "_get_service_credentials",
                                               return_value=service_credentials):
                            # Act
                            azure_clients_manager = AzureClientsManager(cloud_provider=cloud_provider)

                            # Verify
                            self.assertEqual(azure_clients_manager._subscription_id, subscription_id)
                            self.assertEqual(azure_clients_manager._application_id, application_id)
                            self.assertEqual(azure_clients_manager._application_key, application_key)
                            self.assertEqual(azure_clients_manager._tenant, tenant)
                            self.assertEqual(azure_clients_manager._service_credentials, service_credentials)
                            self.assertIsNone(azure_clients_manager._compute_client)
                            self.assertIsNone(azure_clients_manager._network_client)
                            self.assertIsNone(azure_clients_manager._storage_client)
                            self.assertIsNone(azure_clients_manager._resource_client)

    def test_check_params_equality_returns_true(self):
        """Check that method will return True if cloud_provider attributes are the same as in current model"""
        # Act
        with mock.patch("cloudshell.cp.azure.common.azure_clients.ServicePrincipalCredentials"):
            azure_clients_manager = AzureClientsManager(cloud_provider=self.cloud_provider)

        # Verify
        self.assertIs(self.azure_clients_manager, azure_clients_manager)

    def test_check_params_equality_returns_false(self):
        """Check that method will return False if cloud_provider attributes aren't the same as in current model"""
        cloud_provider = mock.MagicMock()
        # Act
        with mock.patch("cloudshell.cp.azure.common.azure_clients.ServicePrincipalCredentials"):
            azure_clients_manager = AzureClientsManager(cloud_provider=cloud_provider)

        # Verify
        self.assertIsNot(self.azure_clients_manager, azure_clients_manager)

    @mock.patch("cloudshell.cp.azure.common.azure_clients.ServicePrincipalCredentials")
    def test_get_service_credentials(self, service_credentials_class):
        """Check that method returns ServicePrincipalCredentials instance"""
        mocked_service_credentials = mock.MagicMock()
        service_credentials_class.return_value = mocked_service_credentials

        # Act
        service_credentials = self.azure_clients_manager._get_service_credentials()

        # Verify
        service_credentials_class.assert_called_once_with(client_id=self.azure_clients_manager._application_id,
                                                          secret=self.azure_clients_manager._application_key,
                                                          tenant=self.azure_clients_manager._tenant)
        self.assertIs(service_credentials, mocked_service_credentials)

    def test_get_subscription(self):
        """"""
        # Act
        subscription = self.azure_clients_manager._get_subscription(self.cloud_provider)
        # Verify
        self.assertEqual(subscription, self.cloud_provider.azure_subscription_id)

    def test_get_azure_application_id(self):
        """"""
        # Act
        azure_application_id = self.azure_clients_manager._get_azure_application_id(self.cloud_provider)
        # Verify
        self.assertEqual(azure_application_id, self.cloud_provider.azure_application_id)

    def test_get_azure_application_key(self):
        """"""
        # Act
        azure_application_key = self.azure_clients_manager._get_azure_application_key(self.cloud_provider)
        # Verify
        self.assertEqual(azure_application_key, self.cloud_provider.azure_application_key)

    def test_get_azure_tenant(self):
        """"""
        # Act
        azure_tenant = self.azure_clients_manager._get_azure_tenant(self.cloud_provider)
        # Verify
        self.assertEqual(azure_tenant, self.cloud_provider.azure_tenant)

    @mock.patch("cloudshell.cp.azure.common.azure_clients.ComputeManagementClient")
    def test_compute_client(self, compute_client_class):
        """Check that property will get ComputeManagementClient client and initialize client only once"""
        mocked_compute_client = mock.MagicMock()
        compute_client_class.return_value = mocked_compute_client
        # Act
        compute_client = self.azure_clients_manager.compute_client
        # repeat property call to verify that method will not create one more instance
        compute_client = self.azure_clients_manager.compute_client

        # Verify
        self.assertIs(compute_client, mocked_compute_client)
        self.assertIs(compute_client, self.azure_clients_manager._compute_client)
        compute_client_class.assert_called_once_with(self.azure_clients_manager._service_credentials,
                                                     self.azure_clients_manager._subscription_id)

    @mock.patch("cloudshell.cp.azure.common.azure_clients.NetworkManagementClient")
    def test_network_client(self, network_client_class):
        """Check that property will get NetworkManagementClient client and initialize client only once"""
        mocked_compute_client = mock.MagicMock()
        network_client_class.return_value = mocked_compute_client
        # Act
        network_client = self.azure_clients_manager.network_client
        # repeat property call to verify that method will not create one more instance
        network_client = self.azure_clients_manager.network_client

        # Verify
        self.assertIs(network_client, mocked_compute_client)
        self.assertIs(network_client, self.azure_clients_manager._network_client)
        network_client_class.assert_called_once_with(self.azure_clients_manager._service_credentials,
                                                     self.azure_clients_manager._subscription_id)

    @mock.patch("cloudshell.cp.azure.common.azure_clients.ResourceManagementClient")
    def test_storage_client(self, resource_client_class):
        """Check that property will get ResourceManagementClient client and initialize client only once"""
        mocked_compute_client = mock.MagicMock()
        resource_client_class.return_value = mocked_compute_client
        # Act
        resource_client = self.azure_clients_manager.resource_client
        # repeat property call to verify that method will not create one more instance
        resource_client = self.azure_clients_manager.resource_client

        # Verify
        self.assertIs(resource_client, mocked_compute_client)
        self.assertIs(resource_client, self.azure_clients_manager._resource_client)
        resource_client_class.assert_called_once_with(self.azure_clients_manager._service_credentials,
                                                      self.azure_clients_manager._subscription_id)

    @mock.patch("cloudshell.cp.azure.common.azure_clients.StorageManagementClient")
    def test_resource_client(self, storage_client_class):
        """Check that property will get StorageManagementClient client and initialize client only once"""
        mocked_compute_client = mock.MagicMock()
        storage_client_class.return_value = mocked_compute_client
        # Act
        storage_client = self.azure_clients_manager.storage_client
        # repeat property call to verify that method will not create one more instance
        storage_client = self.azure_clients_manager.storage_client

        # Verify
        self.assertIs(storage_client, mocked_compute_client)
        self.assertIs(storage_client, self.azure_clients_manager._storage_client)
        storage_client_class.assert_called_once_with(self.azure_clients_manager._service_credentials,
                                                     self.azure_clients_manager._subscription_id)

    @mock.patch("cloudshell.cp.azure.common.azure_clients.SubscriptionClient")
    def test_subscription_client(self, subscription_client_class):
        """Check that property will get SubscriptionClient client and initialize client only once"""
        mocked_subscription_client = mock.MagicMock()
        subscription_client_class.return_value = mocked_subscription_client
        # Act
        subscription_client = self.azure_clients_manager.subscription_client
        # repeat property call to verify that method will not create one more instance
        subscription_client = self.azure_clients_manager.subscription_client

        # Verify
        self.assertIs(subscription_client, mocked_subscription_client)
        self.assertIs(subscription_client, self.azure_clients_manager._subscription_client)
        subscription_client_class.assert_called_once_with(self.azure_clients_manager._service_credentials)
