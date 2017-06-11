from unittest import TestCase

import mock

from cloudshell.cp.azure.common.parsers.azure_model_parser import AzureModelsParser


class TestAzureModelsParser(TestCase):
    def setUp(self):
        self.parser = AzureModelsParser()

    def test_set_base_deploy_azure_vm_model_params_empty_password(self):
        """Check that method set basic params for the deploy VM model from DeployDataHolder"""
        attributes = dict()
        attributes['Add Public IP'] = False
        attributes['Autoload'] = False
        attributes['Inbound Ports'] = 'test'
        attributes['VM Size'] = 'test'
        attributes['Public IP Type'] = 'test'
        attributes['Extension Script file'] = 'test'
        attributes['Extension Script Configurations'] = 'test'
        attributes['Extension Script Timeout'] = '1'
        attributes['Disk Type'] = 'Disk Type'

        data_holder = {'Attributes': attributes,
                       'AppName': mock.MagicMock(),
                       'LogicalResourceRequestAttributes': mock.MagicMock()}

        from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import BaseDeployAzureVMResourceModel
        deploy_azure_vm_model = BaseDeployAzureVMResourceModel()
        logger = mock.Mock()
        cloudshell_session = mock.Mock()

        # Act
        ret = self.parser._set_base_deploy_azure_vm_model_params(
            deployment_resource_model=deploy_azure_vm_model,
            data_holder=data_holder,
            cloudshell_session=cloudshell_session,
            logger=logger)

        # Verify
        self.assertEqual(ret.add_public_ip, attributes['Add Public IP'])
        self.assertEqual(ret.autoload, attributes['Autoload'])
        self.assertEqual(ret.inbound_ports, attributes['Inbound Ports'])
        self.assertEqual(ret.vm_size, attributes['VM Size'])
        self.assertEqual(ret.public_ip_type, attributes['Public IP Type'])
        self.assertEqual(ret.app_name, data_holder['AppName'])
        self.assertEqual(ret.extension_script_file, attributes['Extension Script file'])
        self.assertEqual(ret.extension_script_configurations,
                         attributes['Extension Script Configurations'])



    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.jsonpickle")
    @mock.patch("cloudshell.cp.azure.common.parsers.azure_model_parser.DeployDataHolder")
    def test_set_base_deploy_azure_vm_model_params_with_password(self, deploy_data_holder_class, jsonpickle):
        """Check that method set basic params for the deploy VM model from DeployDataHolder"""
        data_holder = {'Attributes': mock.MagicMock(),
                       'AppName': mock.MagicMock(),
                       'LogicalResourceRequestAttributes': mock.MagicMock()}

        jsonpickle.decode.return_value = data_holder
        # data_holder.ami_params = mock.MagicMock()
        # data_holder.ami_params.password = "secure"
        deploy_data_holder_class.return_value = data_holder
        deploy_azure_vm_model = mock.MagicMock()
        logger = mock.Mock()
        decrypt_result = mock.Mock()
        decrypt_result.Value = "not_secure"
        cloudshell_session = mock.Mock()
        cloudshell_session.DecryptPassword = mock.Mock(return_value=decrypt_result)

        # Act
        self.parser._set_base_deploy_azure_vm_model_params(deployment_resource_model=deploy_azure_vm_model,
                                                                 data_holder=data_holder,
                                                                 cloudshell_session=cloudshell_session,
                                                                 logger=logger)

        # Verify
        data_attributes = data_holder['Attributes']
        self.assertEqual(deploy_azure_vm_model.add_public_ip, data_attributes['Add Public IP'])
        self.assertEqual(deploy_azure_vm_model.autoload, data_attributes['Autoload'])
        self.assertEqual(deploy_azure_vm_model.inbound_ports, data_attributes['Inbound Ports'])
        self.assertEqual(deploy_azure_vm_model.vm_size, data_attributes['Inbound Ports'])
        self.assertEqual(deploy_azure_vm_model.public_ip_type, data_attributes['Public IP Type'])
        self.assertEqual(deploy_azure_vm_model.password, None)
        self.assertEqual(deploy_azure_vm_model.app_name, data_holder['AppName'])
        self.assertEqual(deploy_azure_vm_model.extension_script_file, data_attributes['Extension Script file'])
        self.assertEqual(deploy_azure_vm_model.extension_script_configurations,
                         data_attributes['Extension Script Configurations'])
        self.assertEqual(deploy_azure_vm_model.username, None)
