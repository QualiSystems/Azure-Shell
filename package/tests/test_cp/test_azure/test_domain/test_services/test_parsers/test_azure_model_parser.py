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
    def test_convert_to_deploy_azure_vm_resource_model(self, deploy_data_holder_class, jsonpickle,
                                                       deploy_azure_vm_model_class):
        """Check that method returns DeployAzureVMResourceModel instance with attrs from DeployDataHolder"""
        data_holder = mock.MagicMock()
        deploy_azure_vm_model = mock.MagicMock()
        deploy_data_holder_class.return_value = data_holder
        deployment_request = mock.MagicMock()
        deploy_azure_vm_model_class.return_value = deploy_azure_vm_model

        # Act
        with mock.patch.object(self.tested_class, "_set_base_deploy_azure_vm_model_params") as set_base_params:
            result = self.tested_class.convert_to_deploy_azure_vm_resource_model(deployment_request)

        # Verify
        self.assertIs(result, deploy_azure_vm_model)
        set_base_params.assert_called_once_with(deploy_azure_vm_model, data_holder)

        self.assertEqual(result.image_offer, data_holder.ami_params.image_offer)
        self.assertEqual(result.image_publisher, data_holder.ami_params.image_publisher)
        self.assertEqual(result.image_sku, data_holder.ami_params.image_sku)
        self.assertEqual(result.image_version, data_holder.ami_params.image_version)

    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.jsonpickle")
    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.DeployDataHolder")
    def test_set_base_deploy_azure_vm_model_params(self, deploy_data_holder_class, jsonpickle):
        """Check that method set basic params for the deploy VM model from DeployDataHolder"""
        data_holder = mock.MagicMock()
        deploy_data_holder_class.return_value = data_holder
        deploy_azure_vm_model = mock.MagicMock()

        # Act
        self.tested_class._set_base_deploy_azure_vm_model_params(deploy_azure_vm_model, data_holder)

        # Verify
        self.assertEqual(deploy_azure_vm_model.add_public_ip, data_holder.ami_params.add_public_ip)
        self.assertEqual(deploy_azure_vm_model.autoload, data_holder.ami_params.autoload)
        self.assertEqual(deploy_azure_vm_model.cloud_provider, data_holder.ami_params.cloud_provider)
        self.assertEqual(deploy_azure_vm_model.group_name, data_holder.ami_params.group_name)
        self.assertEqual(deploy_azure_vm_model.inbound_ports, data_holder.ami_params.inbound_ports)
        self.assertEqual(deploy_azure_vm_model.instance_type, data_holder.ami_params.instance_type)
        self.assertEqual(deploy_azure_vm_model.public_ip_type, data_holder.ami_params.public_ip_type)
        self.assertEqual(deploy_azure_vm_model.vm_name, data_holder.ami_params.vm_name)
        self.assertEqual(deploy_azure_vm_model.wait_for_ip, data_holder.ami_params.wait_for_ip)
        self.assertEqual(deploy_azure_vm_model.app_name, data_holder.app_name)

    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser"
                ".DeployAzureVMFromCustomImageResourceModel")
    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.jsonpickle")
    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.DeployDataHolder")
    def test_convert_to_deploy_azure_vm_from_custom_image_resource_model(self,
                                                                         deploy_data_holder_class,
                                                                         jsonpickle,
                                                                         deploy_azure_vm_model_class):
        """Check that method returns DeployAzureVMFromCustomImageResourceModel with attrs from DeployDataHolder"""
        data_holder = mock.MagicMock()
        deploy_azure_vm_model = mock.MagicMock()
        deploy_data_holder_class.return_value = data_holder
        deployment_request = mock.MagicMock()
        deploy_azure_vm_model_class.return_value = deploy_azure_vm_model

        # Act
        with mock.patch.object(self.tested_class, "_set_base_deploy_azure_vm_model_params") as set_base_params:
            result = self.tested_class.convert_to_deploy_azure_vm_from_custom_image_resource_model(deployment_request)

        # Verify
        self.assertIs(result, deploy_azure_vm_model)
        set_base_params.assert_called_once_with(deploy_azure_vm_model, data_holder)
        self.assertEqual(result.image_urn, data_holder.ami_params.image_urn)
        self.assertEqual(result.image_os_type, data_holder.ami_params.image_os_type)

    @mock.patch("cloudshell.cp.azure.domain.services.parsers.azure_model_parser.AzureCloudProviderResourceModel")
    def test_convert_to_cloud_provider_resource_model(self, azure_cp_model_class):
        """Check that method returns AzureCloudProviderResourceModel instance with attrs from context"""
        azure_cp_model = mock.MagicMock()
        azure_cp_model_class.return_value = azure_cp_model
        test_resource = mock.Mock()
        test_resource.attributes = {}
        test_resource.attributes["Azure Client ID"] = test_azure_client_id = mock.MagicMock()
        test_resource.attributes["Azure Secret"] = test_azure_secret = mock.MagicMock()
        test_resource.attributes["Azure Subscription ID"] = test_azure_subscription_id = mock.MagicMock()
        test_resource.attributes["Azure Tenant ID"] = test_azure_tenant = mock.MagicMock()
        test_resource.attributes["Instance Type"] = test_instance_type = mock.MagicMock()
        test_resource.attributes["Networks In Use"] = test_networks_in_use = mock.MagicMock()
        test_resource.attributes["Region"] = "East Canada"
        test_resource.attributes["Management Group Name"] = test_mgmt_group_name = mock.MagicMock()
        cloudshell_session = mock.MagicMock()
        decrypted_azure_secret = mock.MagicMock()
        cloudshell_session.DecryptPassword.return_value = decrypted_azure_secret

        # Act
        result = self.tested_class.convert_to_cloud_provider_resource_model(resource=test_resource,
                                                                            cloudshell_session=cloudshell_session)

        # Verify
        self.assertIs(result, azure_cp_model)
        self.assertEqual(result.azure_client_id, test_azure_client_id)
        self.assertEqual(result.azure_subscription_id, test_azure_subscription_id)
        self.assertEqual(result.azure_tenant, test_azure_tenant)
        self.assertEqual(result.instance_type, test_instance_type)
        self.assertEqual(result.networks_in_use, test_networks_in_use)
        self.assertEqual(result.region, "eastcanada")
        self.assertEqual(result.management_group_name, test_mgmt_group_name)
        self.assertEqual(result.azure_secret, decrypted_azure_secret.Value)

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
