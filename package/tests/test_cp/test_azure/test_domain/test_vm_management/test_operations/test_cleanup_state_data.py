from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.vm_management.operations.cleanup_stale_data import CleanUpStaleDataOperation


class TestAutoloadOperation(TestCase):
    def setUp(self):
        self.network_service = mock.MagicMock()
        self.vm_service = mock.MagicMock()
        self.resource_id_parser = mock.MagicMock()
        self.logger = mock.MagicMock()
        self.cleanup_data_operation = CleanUpStaleDataOperation(network_service=self.network_service,
                                                                vm_service=self.vm_service,
                                                                resource_id_parser=self.resource_id_parser)

    def test_get_connected_resource_groups(self):
        """Check that method will return set with resource group names for related to subnet resources"""
        subnet = mock.MagicMock(ip_configurations=[mock.MagicMock(), mock.MagicMock()])
        expected_res = {"resource_group1", "resource_group2"}

        self.resource_id_parser.get_resource_group_name.side_effect = [
            "resource_group1", "resource_group2", "resource_group2"]

        # Act
        result = self.cleanup_data_operation._get_connected_resource_groups(subnet=subnet)

        # Verify
        self.assertIsInstance(result, set)
        self.assertEqual(result, expected_res)

    def test_get_active_resource_group(self):
        """Check that method will use CloudShell session to retrieve Resource Group names for active reservations"""
        reservation_id = "test_reservation_id"
        cloudshell_session = mock.MagicMock()
        cloudshell_session.GetCurrentReservations.return_value = mock.MagicMock(
            Reservations=[mock.MagicMock(Id=reservation_id)])
        # Act
        result = self.cleanup_data_operation._get_active_resource_group(cloudshell_session=cloudshell_session)

        # Verify
        self.assertIsInstance(result, list)
        self.assertEqual(result, [reservation_id])

    def test_cleanup_stale_data_doesnt_delete_subnet_related_to_active_reservation(self):
        """Check that method will not clean up subnet which is related to the Active reservation's resource group"""
        network_client = mock.MagicMock()
        resource_client = mock.MagicMock()
        cloud_provider_model = mock.MagicMock()
        cloudshell_session = mock.MagicMock()
        self.cleanup_data_operation._get_active_resource_group = mock.MagicMock(return_value=["test_group"])
        self.cleanup_data_operation._get_connected_resource_groups = mock.MagicMock(return_value=["test_group"])

        # Act
        self.cleanup_data_operation.cleanup_stale_data(network_client=network_client,
                                                       resource_client=resource_client,
                                                       cloud_provider_model=cloud_provider_model,
                                                       cloudshell_session=cloudshell_session,
                                                       logger=self.logger)

        # Verify
        self.network_service.delete_subnet.assert_not_called()

    def test_cleanup_stale_data_doesnt_delete_subnet_in_networks_in_use_attr(self):
        """Check that method will not clean up subnet which is listed in the "Networks In Use" attribute"""
        network_client = mock.MagicMock()
        resource_client = mock.MagicMock()
        cloud_provider_model = mock.MagicMock(networks_in_use=["10.10.10.10/24"])
        cloudshell_session = mock.MagicMock()
        subnet = mock.MagicMock(address_prefix="10.10.10.10/24")
        sandbox_vnet = mock.MagicMock(subnets=[subnet])
        self.network_service.get_sandbox_virtual_network.return_value = sandbox_vnet
        self.cleanup_data_operation._get_connected_resource_groups = mock.MagicMock()

        # Act
        self.cleanup_data_operation.cleanup_stale_data(network_client=network_client,
                                                       resource_client=resource_client,
                                                       cloud_provider_model=cloud_provider_model,
                                                       cloudshell_session=cloudshell_session,
                                                       logger=self.logger)

        # Verify
        self.network_service.delete_subnet.assert_not_called()

    def test_cleanup_stale_data(self):
        """Check that method will clean up subnet and related resource groups"""
        network_client = mock.MagicMock()
        resource_client = mock.MagicMock()
        cloud_provider_model = mock.MagicMock()
        cloudshell_session = mock.MagicMock()
        subnet = mock.MagicMock(address_prefix="10.10.10.10/24")
        sandbox_vnet = mock.MagicMock(subnets=[subnet])
        self.network_service.get_sandbox_virtual_network.return_value = sandbox_vnet


        # Act
        self.cleanup_data_operation.cleanup_stale_data(network_client=network_client,
                                                       resource_client=resource_client,
                                                       cloud_provider_model=cloud_provider_model,
                                                       cloudshell_session=cloudshell_session,
                                                       logger=self.logger)

        # Verify
        self.network_service.get_sandbox_virtual_network.assert_called_once_with(
            group_name=cloud_provider_model.management_group_name,
            network_client=network_client)

        self.network_service.delete_subnet.assert_called_once_with(
            group_name=cloud_provider_model.management_group_name,
            network_client=network_client,
            subnet_name=subnet.name,
            vnet_name=sandbox_vnet.name)

        self.network_service.update_subnet.assert_called_once_with(
            network_client=network_client,
            resource_group_name=cloud_provider_model.management_group_name,
            virtual_network_name=sandbox_vnet.name,
            subnet_name=subnet.name,
            subnet=subnet)

        self.vm_service.delete_resource_group.assert_called_once_with(
            resource_management_client=resource_client,
            group_name=self.resource_id_parser.get_resource_group_name())
