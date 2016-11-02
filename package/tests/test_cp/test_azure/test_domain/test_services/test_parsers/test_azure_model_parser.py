from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.services.parsers.azure_model_parser import AzureModelsParser


class TestAzureModelsParser(TestCase):
    def setUp(self):
        self.tested_class = AzureModelsParser

    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.jsonpickle")
    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.DeployDataHolder")
    def test_convert_app_resource_to_deployed_app(self, deploy_data_holder_class, jsonpickle):
        """Check that method will convert string to DeployDataHolder model"""
        resource = mock.MagicMock()
        decoded_data = mock.MagicMock()
        deployed_app = mock.MagicMock()
        jsonpickle.decode.return_value = decoded_data
        deploy_data_holder_class.return_value = deployed_app

        # Act
        result = self.tested_class.convert_app_resource_to_deployed_app(resource)

        # Verify
        deploy_data_holder_class.assert_called_once_with(decoded_data)
        self.assertEqual(result, deployed_app)

    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.DeployAzureVMResourceModel")
    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.jsonpickle")
    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.DeployDataHolder")
    def test_convert_to_deployment_resource_model(self, deploy_data_holder_class, jsonpickle,
                                                  deploy_azure_vm_model_class):
        """Check that method returns DeployAzureVMResourceModel instance with attrs from DeployDataHolder"""
        data_holder = mock.MagicMock()
        deploy_azure_vm_model = mock.MagicMock()
        deploy_data_holder_class.return_value = data_holder
        deployment_request = mock.MagicMock()
        deploy_azure_vm_model_class.return_value = deploy_azure_vm_model

        # Act
        result = self.tested_class.convert_to_deployment_resource_model(deployment_request)

        # Verify
        self.assertIs(result, deploy_azure_vm_model)
        self.assertEqual(result.add_public_ip, data_holder.ami_params.add_public_ip)
        self.assertEqual(result.autoload, data_holder.ami_params.autoload)
        self.assertEqual(result.cloud_provider, data_holder.ami_params.cloud_provider)
        self.assertEqual(result.disk_type, data_holder.ami_params.disk_type)
        self.assertEqual(result.group_name, data_holder.ami_params.group_name)
        self.assertEqual(result.image_offer, data_holder.ami_params.image_offer)
        self.assertEqual(result.image_publisher, data_holder.ami_params.image_publisher)
        self.assertEqual(result.image_sku, data_holder.ami_params.image_sku)
        self.assertEqual(result.inbound_ports, data_holder.ami_params.inbound_ports)
        self.assertEqual(result.instance_type, data_holder.ami_params.instance_type)
        self.assertEqual(result.outbound_ports, data_holder.ami_params.outbound_ports)
        self.assertEqual(result.public_ip_type, data_holder.ami_params.public_ip_type)
        self.assertEqual(result.vm_name, data_holder.ami_params.vm_name)
        self.assertEqual(result.wait_for_ip, data_holder.ami_params.wait_for_ip)
        self.assertEqual(result.app_name, data_holder.app_name)

    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.AzureCloudProviderResourceModel")
    def test_convert_to_cloud_provider_resource_model(self, azure_cp_model_class):
        """Check that method returns AzureCloudProviderResourceModel instance with attrs from context"""
        azure_cp_model = mock.MagicMock()
        azure_cp_model_class.return_value = azure_cp_model
        test_resource = mock.Mock()
        test_resource.attributes = {}
        test_resource.attributes["Azure Client ID"] = test_azure_client_id = mock.MagicMock()
        test_resource.attributes["Azure Mgmt Network ID"] = test_azure_mgmt_id = mock.MagicMock()
        test_resource.attributes["Azure Mgmt NSG ID"] = test_azure_mgmt_nsg_id = mock.MagicMock()
        test_resource.attributes["Azure Secret"] = test_azure_secret = mock.MagicMock()
        test_resource.attributes["Azure Subscription ID"] = test_azure_subscription_id = mock.MagicMock()
        test_resource.attributes["Azure Tenant"] = test_azure_tenant = mock.MagicMock()
        test_resource.attributes["Instance Type"] = test_instance_type = mock.MagicMock()
        test_resource.attributes["Keypairs Location"] = test_keypairts_location = mock.MagicMock()
        test_resource.attributes["Networks In Use"] = test_networks_in_use = mock.MagicMock()
        test_resource.attributes["Region"] = test_region = mock.MagicMock()
        test_resource.attributes["Storage Type"] = test_storage_type = mock.MagicMock()
        test_resource.attributes["Management Group Name"] = test_mgmt_group_name = mock.MagicMock()

        # Act
        result = self.tested_class.convert_to_cloud_provider_resource_model(test_resource)

        # Verify
        self.assertIs(result, azure_cp_model)
        self.assertEqual(result.azure_client_id, test_azure_client_id)
        self.assertEqual(result.azure_mgmt_network_d, test_azure_mgmt_id)
        self.assertEqual(result.azure_mgmt_nsg_id, test_azure_mgmt_nsg_id)
        self.assertEqual(result.azure_secret, test_azure_secret)
        self.assertEqual(result.azure_subscription_id, test_azure_subscription_id)
        self.assertEqual(result.azure_tenant, test_azure_tenant)
        self.assertEqual(result.instance_type, test_instance_type)
        self.assertEqual(result.keypairs_location, test_keypairts_location)
        self.assertEqual(result.networks_in_use, test_networks_in_use)
        self.assertEqual(result.region, test_region)
        self.assertEqual(result.storage_type, test_storage_type)
        self.assertEqual(result.management_group_name, test_mgmt_group_name)

    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.ReservationModel")
    def test_convert_to_reservation_model(self, reservation_model_class):
        """Check that method will return ReservationModel instance from given context"""
        reservation_model = mock.MagicMock()
        reservation_model_class.return_value = reservation_model
        reservation_context = mock.MagicMock()

        # Act
        result = self.tested_class.convert_to_reservation_model(reservation_context)

        # Verify
        self.assertIs(result, reservation_model)
        reservation_model_class.assert_called_once_with(reservation_context)

    def test_get_public_ip_from_connected_resource_details(self):
        """Check that method will return Public IP attr from the context"""
        public_ip = mock.MagicMock()
        resource_context = mock.MagicMock(remote_endpoints=[
            mock.MagicMock(attributes={"Public IP": public_ip})])

        # Act
        result = self.tested_class.get_public_ip_from_connected_resource_details(resource_context)

        # Verify
        self.assertIs(result, public_ip)

    def test_get_private_ip_from_connected_resource_details(self):
        """Check that method will return Private IP attr from the context"""
        private_ip = mock.MagicMock()
        resource_context = mock.MagicMock(remote_endpoints=[mock.MagicMock(address=private_ip)])

        # Act
        result = self.tested_class.get_private_ip_from_connected_resource_details(resource_context)

        # Verify
        self.assertIs(result, private_ip)

    def test_get_connected_resource_fullname(self):
        """Check that method will return fullname from the resource context"""
        fullname = mock.MagicMock()
        resource_context = mock.MagicMock(remote_endpoints=[mock.MagicMock(fullname=fullname)])

        # Act
        result = self.tested_class.get_connected_resource_fullname(resource_context)

        # Verify
        self.assertIs(result, fullname)
