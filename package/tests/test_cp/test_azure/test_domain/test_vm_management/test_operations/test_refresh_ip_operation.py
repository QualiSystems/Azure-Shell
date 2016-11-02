from unittest import TestCase

from msrestazure.azure_exceptions import CloudError
import mock

from cloudshell.cp.azure.domain.vm_management.operations.refresh_ip_operation import RefreshIPOperation


class TestRefreshIPOperation(TestCase):
    def setUp(self):
        self.logger = mock.MagicMock()
        self.cloudshell_session = mock.MagicMock()
        self.compute_client = mock.MagicMock()
        self.network_client = mock.MagicMock()
        self.resource_group_name = "test_resource_group_name"
        self.resource_fullname = "test_resource_fullname"
        self.vm_name = "test_vm_name"
        self.private_ip_on_resource = "10.0.0.1"
        self.public_ip_on_resource = "172.29.128.255"

        self.refresh_ip_operation = RefreshIPOperation(logger=self.logger)

    def test_refresh_ip(self):
        """Check that method uses network client to get public IP value and updates it on CloudShell"""
        self.network_client.public_ip_addresses.get.return_value = public_ip_from_azure = mock.MagicMock()
        self.network_client.network_interfaces.get.return_value = nic = mock.MagicMock()

        # Act
        self.refresh_ip_operation.refresh_ip(
            cloudshell_session=self.cloudshell_session,
            compute_client=self.compute_client,
            network_client=self.network_client,
            resource_group_name=self.resource_group_name,
            vm_name=self.vm_name,
            private_ip_on_resource=self.private_ip_on_resource,
            public_ip_on_resource=self.public_ip_on_resource,
            resource_fullname=self.resource_fullname)

        # Verify
        self.network_client.public_ip_addresses.get.assert_called_once_with(self.resource_group_name, self.vm_name)
        self.cloudshell_session.SetAttributeValue.assert_called_once_with(self.resource_fullname, "Public IP",
                                                                          public_ip_from_azure.ip_address)

        self.cloudshell_session.UpdateResourceAddress.assert_called_once_with(
            self.resource_fullname, nic.ip_configurations[0].private_ip_address)

    def test_refresh_ip_no_public_ip_on_azure(self):
        """Check that method handles Azure CloudError exception (no Public IP on Azure)"""
        self.network_client.network_interfaces.get.return_value = nic = mock.MagicMock()
        self.network_client.public_ip_addresses.get.side_effect = CloudError(mock.MagicMock())

        # Act
        self.refresh_ip_operation.refresh_ip(
            cloudshell_session=self.cloudshell_session,
            compute_client=self.compute_client,
            network_client=self.network_client,
            resource_group_name=self.resource_group_name,
            vm_name=self.vm_name,
            private_ip_on_resource=self.private_ip_on_resource,
            public_ip_on_resource=self.public_ip_on_resource,
            resource_fullname=self.resource_fullname)

        # Verify
        self.network_client.public_ip_addresses.get.assert_called_once_with(self.resource_group_name, self.vm_name)
        self.cloudshell_session.SetAttributeValue.assert_called_once_with(self.resource_fullname, "Public IP", "")

        self.cloudshell_session.UpdateResourceAddress.assert_called_once_with(
            self.resource_fullname, nic.ip_configurations[0].private_ip_address)

    def test_refresh_ip_does_not_update_ips(self):
        """Check that method will not update private/public IPs on the CloudShell if they are same as on Azure"""
        self.network_client.public_ip_addresses.get.return_value = mock.MagicMock(ip_address=self.public_ip_on_resource)
        self.network_client.network_interfaces.get.return_value = mock.MagicMock(
            ip_configurations=[mock.MagicMock(private_ip_address=self.private_ip_on_resource)])

        # Act
        self.refresh_ip_operation.refresh_ip(
            cloudshell_session=self.cloudshell_session,
            compute_client=self.compute_client,
            network_client=self.network_client,
            resource_group_name=self.resource_group_name,
            vm_name=self.vm_name,
            private_ip_on_resource=self.private_ip_on_resource,
            public_ip_on_resource=self.public_ip_on_resource,
            resource_fullname=self.resource_fullname)

        # Verify
        self.network_client.public_ip_addresses.get.assert_called_once_with(self.resource_group_name, self.vm_name)
        self.cloudshell_session.SetAttributeValue.assert_not_called()
        self.cloudshell_session.UpdateResourceAddress.assert_not_called()
