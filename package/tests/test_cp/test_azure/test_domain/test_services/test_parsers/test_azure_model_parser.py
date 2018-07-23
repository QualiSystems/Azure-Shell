from unittest import TestCase

import mock

from cloudshell.cp.azure.common.parsers.azure_model_parser import AzureModelsParser


class TestAzureModelsParser(TestCase):
    def setUp(self):
        self.tested_class = AzureModelsParser

    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.jsonpickle")
    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.DeployDataHolder")
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

    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.DeployAzureVMResourceModel")
    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.jsonpickle")
    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.DeployDataHolder")
    def test_convert_to_deploy_azure_vm_resource_model(self, deploy_data_holder_class, jsonpickle,
                                                       deploy_azure_vm_model_class):
        """Check that method returns DeployAzureVMResourceModel instance with attrs from DeployDataHolder"""
        data_holder = {'Attributes': mock.MagicMock(), 'AppName': mock.MagicMock()}
        deploy_azure_vm_model = mock.MagicMock()
        deploy_data_holder_class.return_value = data_holder
        deployment_request = mock.MagicMock()
        deploy_azure_vm_model_class.return_value = deploy_azure_vm_model
        jsonpickle.decode.return_value = data_holder
        logger = mock.Mock()
        cloudshell_session = mock.Mock()

        # Act
        with mock.patch.object(self.tested_class, "_set_base_deploy_azure_vm_model_params") as set_base_params:
            result = self.tested_class.convert_to_deploy_azure_vm_resource_model(deployment_request,
                                                                                 cloudshell_session,
                                                                                 logger)

            # Verify
            self.assertIs(result, deploy_azure_vm_model)

            data_attributes = data_holder['Attributes']
            self.assertEqual(result.image_offer, data_attributes['Image Offer'])
            self.assertEqual(result.image_publisher, data_attributes['Image Publisher'])
            self.assertEqual(result.image_sku, data_attributes['Image SKU'])
            self.assertEqual(result.image_version, data_attributes['Image Version'])

    def test_convert_base_hadels_2nd_gen_shell_attributes(self):
        # arrange
        cloudshell_session = mock.Mock()
        cloudshell_session.DecryptPassword = mock.Mock(return_value=mock.Mock(Value='my_pass'))

        logger = mock.Mock()
        deployment_resource_model = mock.MagicMock()
        data_holder = mock.MagicMock()

        attributes_dict = {'some_namespace.User': 'my_user',
                           'some_namespace.Password': 'my_encrypted_pass'}
        d = {'Attributes': mock.MagicMock(),
             'AppName': 'some_app_name',
             'LogicalResourceRequestAttributes': attributes_dict}

        data_holder.__getitem__.side_effect = d.__getitem__
        data_holder.__iter__.side_effect = d.__iter__

        # act
        result = AzureModelsParser._set_base_deploy_azure_vm_model_params(
            deployment_resource_model=deployment_resource_model,
            data_holder=data_holder,
            cloudshell_session=cloudshell_session,
            logger=logger)

        # assert
        self.assertEqual(result.username, 'my_user')
        self.assertEqual(result.password, 'my_pass')

    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.DeployAzureVMFromCustomImageResourceModel")
    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.jsonpickle")
    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.DeployDataHolder")
    def test_convert_to_deploy_azure_vm_from_custom_image_resource_model(self,
                                                                         deploy_data_holder_class,
                                                                         jsonpickle,
                                                                         deploy_azure_vm_model_class):
        """Check that method returns DeployAzureVMFromCustomImageResourceModel with attrs from DeployDataHolder"""
        data_holder = {'Attributes': mock.MagicMock()}
        deploy_azure_vm_model = mock.MagicMock()
        deploy_data_holder_class.return_value = data_holder
        deployment_request = mock.MagicMock()
        deploy_azure_vm_model_class.return_value = deploy_azure_vm_model
        logger = mock.Mock()
        cloudshell_session = mock.Mock()
        jsonpickle.decode.return_value = data_holder

        # Act
        self.tested_class._set_base_deploy_azure_vm_model_params = mock.MagicMock()
        # with mock.patch.object(self.tested_class, "_set_base_deploy_azure_vm_model_params") as set_base_params:
        result = self.tested_class.convert_to_deploy_azure_vm_from_custom_image_resource_model(deployment_request,
                                                                                               cloudshell_session,
                                                                                               logger)
        # Verify
        self.assertIs(result, deploy_azure_vm_model)

        self.tested_class._set_base_deploy_azure_vm_model_params.assert_called_once_with(
            deployment_resource_model=deploy_azure_vm_model,
            data_holder=data_holder,
            cloudshell_session=cloudshell_session,
            logger=logger)

        att = data_holder['Attributes']
        self.assertEqual(result.image_name, att['Azure Image'])
        self.assertEqual(result.image_resource_group, att['Azure Resource Group'])

    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.AzureCloudProviderResourceModel")
    def test_convert_to_cloud_provider_resource_model(self, azure_cp_model_class):
        """Check that method returns AzureCloudProviderResourceModel instance with attrs from context"""
        azure_cp_model = mock.MagicMock()
        azure_cp_model_class.return_value = azure_cp_model
        test_resource = mock.Mock()
        test_resource.attributes = {}
        test_resource.attributes["Azure Application ID"] = test_azure_application_id = mock.MagicMock()
        test_resource.attributes["Azure Application Key"] = test_azure_application_key = mock.MagicMock()
        test_resource.attributes["Additional Mgmt Networks"] = " mgmt_network1, mgmt_network2"
        test_resource.attributes["Azure Subscription ID"] = test_azure_subscription_id = mock.MagicMock()
        test_resource.attributes["Azure Tenant ID"] = test_azure_tenant = mock.MagicMock()
        test_resource.attributes["VM Size"] = test_vm_size = mock.MagicMock()
        test_resource.attributes["Networks In Use"] = "network1,  network2 "
        test_resource.attributes["Region"] = "East Canada"
        test_resource.attributes["Management Group Name"] = test_mgmt_group_name = mock.MagicMock()
        test_resource.attributes["Execution Server Selector"] = ""
        cloudshell_session = mock.MagicMock()
        decrypted_azure_application_key = mock.MagicMock()
        cloudshell_session.DecryptPassword.return_value = decrypted_azure_application_key

        # Act
        result = self.tested_class.convert_to_cloud_provider_resource_model(resource=test_resource,
                                                                            cloudshell_session=cloudshell_session)

        # Verify
        self.assertIs(result, azure_cp_model)
        self.assertEqual(result.azure_application_id, test_azure_application_id)
        self.assertEqual(result.azure_subscription_id, test_azure_subscription_id)
        self.assertEqual(result.azure_tenant, test_azure_tenant)
        self.assertEqual(result.vm_size, test_vm_size)
        self.assertEqual(result.networks_in_use, ["network1", "network2"])
        self.assertEqual(result.region, "eastcanada")
        self.assertEqual(result.management_group_name, test_mgmt_group_name)
        self.assertEqual(result.additional_mgmt_networks, ["mgmt_network1", "mgmt_network2"])
        self.assertEqual(result.azure_application_key, decrypted_azure_application_key.Value)

    def test_convert_list_attribute(self):
        """Check that method will convert sting attribute into the list"""
        attribute = "param1 , param2, param3 "

        # Act
        result = self.tested_class._convert_list_attribute(attribute)

        # Verify
        self.assertEqual(result, ["param1", "param2", "param3"])

    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.ReservationModel")
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
