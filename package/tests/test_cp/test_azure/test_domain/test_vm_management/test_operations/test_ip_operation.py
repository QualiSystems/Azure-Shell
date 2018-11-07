from unittest import TestCase
from mock import Mock, MagicMock
from msrestazure.azure_exceptions import CloudError
from requests import Response

from cloudshell.cp.azure.domain.networking_management.operations.ip_operation import IPAddressOperation


class TestIpOperation(TestCase):
    def setUp(self):
        self.mocks = Mock()
        self.mocks.ip_service = Mock()
        self.mocks.logger = Mock()
        self.mocks.cloudshell_session = Mock()
        self.mocks.cloud_provider_model = Mock()
        self.mocks.cloud_provider_model.private_ip_allocation_method = 'cloudshell allocation'
        self.mocks.network_client = Mock()
        self.mocks.reservation_id = Mock()
        self.mocks.subnet_cidr = Mock()
        self.mocks.owner = Mock()
        self.mocks.network_service = Mock()
        self.mocks.name_provider_service = Mock()
        self.ip_operation = IPAddressOperation(self.mocks.ip_service,
                                               self.mocks.network_service,
                                               self.mocks.name_provider_service)

    def test_get_available_private_ip_returns_next_available_ip_from_cs_pool(self):
        # Prepare
        m = self.mocks

        ip_address = '1.2.3.4'
        m.ip_service.get_next_available_ip_from_cs_pool.return_value = ip_address

        result = self.ip_operation.get_available_private_ip(
            m.logger,
            m.cloudshell_session,
            m.cloud_provider_model,
            m.network_client,
            m.reservation_id,
            m.subnet_cidr,
            m.owner
        )

        # Verify
        self.assertEqual(ip_address, result)

    def test_get_available_private_ip_blocked_when_cloud_provider_uses_static(self):
        # Prepare
        m = self.mocks

        m.cloud_provider_model.private_ip_allocation_method = 'Azure Allocation'
        error_message = "GetAvailablePrivateIP is supported only when the cloud provider " \
                        "'Private IP Allocation Method' attribute is set to Cloudshell Allocation. Current allocation method is {}" \
            .format(m.cloud_provider_model.private_ip_allocation_method)

        # Verify
        self.assertRaisesRegexp(ValueError, error_message, self.ip_operation.get_available_private_ip,
                                m.logger,
                                m.cloudshell_session,
                                m.cloud_provider_model,
                                m.network_client,
                                m.reservation_id,
                                m.subnet_cidr,
                                m.owner)

    def test_get_available_private_ip_fails_when_accessing_non_existent_subnet(self):
        # Prepare
        m = self.mocks
        error_message = 'Requested subnet {} doesnt exist in reservation {}'.format(m.subnet_cidr,
                                                                                    m.reservation_id)
        response = Response()
        response.reason = "Not Found"
        m.network_client.subnets.get.side_effect = CloudError(response)

        # Verify
        self.assertRaises(CloudError, self.ip_operation.get_available_private_ip,
                          m.logger,
                          m.cloudshell_session,
                          m.cloud_provider_model,
                          m.network_client,
                          m.reservation_id,
                          m.subnet_cidr,
                          m.owner)

        m.logger.exception.assert_called_with(error_message)
