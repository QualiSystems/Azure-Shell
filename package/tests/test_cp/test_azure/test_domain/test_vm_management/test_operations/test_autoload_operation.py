from unittest import TestCase

import mock
from msrest.exceptions import AuthenticationError
from msrestazure.azure_exceptions import CloudError

from cloudshell.cp.azure.domain.vm_management.operations.autoload_operation import AutoloadOperation
from cloudshell.cp.azure.common.exceptions.autoload_exception import AutoloadException


class TestAutoloadOperation(TestCase):
    def setUp(self):
        self.vm_service = mock.MagicMock()
        self.subscription_service = mock.MagicMock()
        self.network_service = mock.MagicMock()
        self.tags_service = mock.MagicMock()
        self.logger = mock.MagicMock()
        self.autoload_operation = AutoloadOperation(subscription_service=self.subscription_service,
                                                    vm_service=self.vm_service,
                                                    network_service=self.network_service)

    @mock.patch("cloudshell.cp.azure.domain.vm_management.operations.autoload_operation.AutoLoadDetails")
    def test_get_inventory(self, autoload_details_class):
        """Check that method will return AutoLoadDetails instance"""
        cloud_provider_model = mock.MagicMock()
        autoload_details = mock.MagicMock()
        autoload_details_class.return_value = autoload_details

        self.autoload_operation._validate_region = mock.MagicMock()
        self.autoload_operation._validate_api_credentials = mock.MagicMock()
        self.autoload_operation._register_azure_providers = mock.MagicMock()
        self.autoload_operation._validate_mgmt_resource_group = mock.MagicMock()
        self.autoload_operation._validate_vnet = mock.MagicMock()
        self.autoload_operation._validate_vm_size = mock.MagicMock()
        self.autoload_operation._validate_additional_mgmt_networks = mock.MagicMock()

        # Act
        result = self.autoload_operation.get_inventory(cloud_provider_model=cloud_provider_model,
                                                       logger=self.logger)
        # Verify
        self.assertEqual(result, autoload_details)
        self.autoload_operation._validate_region.assert_called_once()
        self.autoload_operation._validate_api_credentials.assert_called_once()
        self.autoload_operation._register_azure_providers.assert_called_once()
        self.autoload_operation._validate_mgmt_resource_group.assert_called_once()
        self.autoload_operation._validate_vnet.assert_called()
        self.autoload_operation._validate_vm_size.assert_called_once()
        self.autoload_operation._validate_additional_mgmt_networks.assert_called_once()

    @mock.patch("cloudshell.cp.azure.domain.vm_management.operations.autoload_operation.AzureClientsManager")
    def test_validate_api_credentials(self, azure_clients_manager_class):
        """Check that method will raise AutoloadException if Azure API credentials aren't valid"""
        cloud_provider_model = mock.MagicMock()
        azure_clients_manager_class.side_effect = AuthenticationError(mock.MagicMock())

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_api_credentials(cloud_provider_model=cloud_provider_model,
                                                              logger=self.logger)
        # Verify
        self.assertEqual(ex.exception.message, "Failed to connect to Azure API, please check the log for more details")

    def test_validate_region(self):
        """Check that method will not raise AutoloadException if region is a valid Azure Geo-location"""
        subscription_client = mock.MagicMock()
        subscription_id = "subscription ID"
        region = "valid region"
        valid_region = mock.MagicMock()
        valid_region.name = region
        self.subscription_service.list_available_regions.return_value = [valid_region]

        # Act
        self.autoload_operation._validate_region(subscription_client=subscription_client,
                                                 subscription_id=subscription_id,
                                                 region=region)

        # Verify
        self.subscription_service.list_available_regions.assert_called_once_with(
            subscription_client=subscription_client,
            subscription_id=subscription_id)

    def test_validate_region_is_empty(self):
        """Check that method will raise AutoloadException if region is empty"""
        subscription_client = mock.MagicMock()
        subscription_id = "subscription ID"

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_region(subscription_client=subscription_client,
                                                     subscription_id=subscription_id,
                                                     region="")

        # Verify
        self.assertEqual(ex.exception.message, "Region attribute can not be empty")

    def test_validate_region_is_invalid(self):
        """Check that method will raise AutoloadException if region is invalid Azure Geo-location"""
        subscription_client = mock.MagicMock()
        subscription_id = "subscription ID"
        region = "invalid region"

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_region(subscription_client=subscription_client,
                                                     subscription_id=subscription_id,
                                                     region=region)

        # Verify
        self.assertEqual(ex.exception.message, 'Region "{}" is not a valid Azure Geo-location'.format(region))
        self.subscription_service.list_available_regions.assert_called_once_with(
            subscription_client=subscription_client,
            subscription_id=subscription_id)

    def test_validate_mgmt_resource_group_not_found(self):
        """Check that method will raise AutoloadException if management resource group doesn't exist on Azure"""
        resource_client = mock.MagicMock()
        mgmt_group_name = "test_group_name"
        region = "test_region"
        self.vm_service.get_resource_group.side_effect = CloudError(mock.MagicMock())

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_mgmt_resource_group(resource_client=resource_client,
                                                                  mgmt_group_name=mgmt_group_name,
                                                                  region=region,
                                                                  logger=self.logger)
        # Verify
        self.assertEqual(ex.exception.message, "Failed to find Management group {}".format(mgmt_group_name))

    def test_validate_mgmt_resource_group_not_in_provided_region(self):
        """Check that method will raise AutoloadException if management resource group is not in the provided region"""
        resource_client = mock.MagicMock()
        mgmt_group_name = "test_group_name"
        region = "test_region"

        resource_group = mock.MagicMock(location="some_other_region")
        self.vm_service.get_resource_group.return_value = resource_group

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_mgmt_resource_group(resource_client=resource_client,
                                                                  mgmt_group_name=mgmt_group_name,
                                                                  region=region,
                                                                  logger=self.logger)
        # Verify
        self.assertEqual(ex.exception.message, "Management group {} is not under the {} region".format(mgmt_group_name,
                                                                                                       region))

    def test_validate_vnet(self,):
        """Check that method will raise AutoloadException if MGMT resource group doesn't contain some vNet"""
        virtual_networks = mock.MagicMock()
        mgmt_group_name = "test_group_name"
        network_tag = "some_tag_value"
        self.network_service.get_virtual_network_by_tag.return_value = None

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_vnet(virtual_networks=virtual_networks,
                                                   mgmt_group_name=mgmt_group_name,
                                                   network_tag=network_tag,
                                                   logger=self.logger)
        # Verify
        self.assertEqual(ex.exception.message, 'Failed to find Vnet with network type "{}" tag under Management '
                                               'group {}'.format(network_tag,
                                                                 mgmt_group_name))

    def test_validate_vm_size(self):
        """Check that method will raise AutoloadException if "Instance Type" attribute is invalid"""
        compute_client = mock.MagicMock()
        region = "southcentralus"
        vm_size = "Basic_A0_INVALID"
        self.vm_service.list_virtual_machine_sizes.return_value = []

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_vm_size(compute_client=compute_client,
                                                      region=region,
                                                      vm_size=vm_size)
        # Verify
        self.assertEqual(ex.exception.message, "VM Size {} is not valid".format(vm_size))

    def test_register_azure_providers(self):
        """Check that method will use resource client to register Azure providers"""
        resource_client = mock.MagicMock()

        # Act
        self.autoload_operation._register_azure_providers(resource_client=resource_client, logger=self.logger)

        # Verify
        resource_client.providers.register.assert_has_calls([
            mock.call("Microsoft.Authorization"),
            mock.call("Microsoft.Storage"),
            mock.call("Microsoft.Network"),
            mock.call("Microsoft.Compute")])

    def test_validate_networks_in_use_not_all_sandbox_subnets_listed(self):
        """Check that method will raise AutoloadException if "Networks In Use" attribute is invalid

        Verify that all subnets in the "sandbox" vNet are listed in the attribute"""
        self.autoload_operation._validate_cidr_format = mock.MagicMock(return_value=True)
        networks_in_use = ["network2", "network4"]
        sandbox_vnet = mock.MagicMock(subnets=[mock.MagicMock(address_prefix="network1"),
                                               mock.MagicMock(address_prefix="network2")])

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_networks_in_use(sandbox_vnet=sandbox_vnet,
                                                              networks_in_use=networks_in_use,
                                                              logger=self.logger)
        # Verify
        self.assertEqual(ex.exception.message, 'The following subnets "network1" were found under the "{}" VNet '
                                               'in Azure and should be set in the "Network In Use" field.'
                         .format(sandbox_vnet.name))

        self.autoload_operation._validate_cidr_format.assert_any_call("network2", self.logger)
        self.autoload_operation._validate_cidr_format.assert_any_call("network4", self.logger)

    def test_validate_networks_in_use_with_invalid_cidr_format(self):
        """Check that method will raise AutoloadException if "Networks In Use" attribute have invalid CIDR format"""
        self.autoload_operation._validate_cidr_format = mock.MagicMock(return_value=False)
        networks_in_use = ["network2", "network4"]
        sandbox_vnet = mock.MagicMock()

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_networks_in_use(sandbox_vnet=sandbox_vnet,
                                                              networks_in_use=networks_in_use,
                                                              logger=self.logger)
        # Verify
        self.assertEqual(ex.exception.message, 'CIDR network2 under the "Networks In Use" attribute '
                                               'is not in the valid format')

    def test_validate_cidr_format(self):
        """Check that method will return True is CIDR format is valid"""
        cidr = "10.10.10.10/24"

        result = self.autoload_operation._validate_cidr_format(cidr=cidr, logger=self.logger)

        self.assertTrue(result)

    def test_validate_cidr_format_invalid(self):
        """Check that method will return False if given CIDR format is valid"""
        cidr = "invalid CIDR"

        result = self.autoload_operation._validate_cidr_format(cidr=cidr, logger=self.logger)

        self.assertFalse(result)

    def test_validate_cidr_format_single_ip(self):
        """Check that method will return False if given CIDR is a single IP address"""
        cidr = "10.10.10.10"

        result = self.autoload_operation._validate_cidr_format(cidr=cidr, logger=self.logger)

        self.assertFalse(result)

    def test_validate_additional_mgmt_networks(self):
        """Check that method will raise AutoloadException if "Additional Mgmt Networks" attr have invalid CIDR format"""
        self.autoload_operation._validate_cidr_format = mock.MagicMock(return_value=False)
        additional_mgmt_networks = ["network2", "network4"]

        # Act
        with self.assertRaises(AutoloadException) as ex:
            self.autoload_operation._validate_additional_mgmt_networks(
                additional_mgmt_networks=additional_mgmt_networks,
                logger=self.logger)
        # Verify
        self.assertEqual(ex.exception.message, 'CIDR network2 under the "Additional Mgmt Networks" attribute '
                                               'is not in the valid format')
