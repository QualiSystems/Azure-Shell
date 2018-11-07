from unittest import TestCase

import mock
from azure.mgmt.network.models import SecurityRule
from cloudshell.cp.core.models import DeployApp

from cloudshell.cp.azure.azure_shell import AzureShell
from cloudshell.cp.azure.models.app_security_groups_model import AppSecurityGroupModel
from cloudshell.cp.azure.models.ssh_key import SSHKey


class TestAzureShell(TestCase):
    @mock.patch("cloudshell.cp.azure.azure_shell.AutoloadOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.DeployedAppPortsOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.CommandResultsParser")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureModelsParser")
    @mock.patch("cloudshell.cp.azure.azure_shell.VirtualMachineService")
    @mock.patch("cloudshell.cp.azure.azure_shell.NetworkService")
    @mock.patch("cloudshell.cp.azure.azure_shell.StorageService")
    @mock.patch("cloudshell.cp.azure.azure_shell.TagService")
    @mock.patch("cloudshell.cp.azure.azure_shell.KeyPairService")
    @mock.patch("cloudshell.cp.azure.azure_shell.SecurityGroupService")
    @mock.patch("cloudshell.cp.azure.azure_shell.PrepareSandboxInfraOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.DeployAzureVMOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.PowerAzureVMOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.RefreshIPOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.DeleteAzureVMOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.AccessKeyOperation")
    def setUp(self, access_key_operation, delete_azure_vm_operation, refresh_ip_operation, power_azure_vm_operation,
              deploy_azure_vm_operation, prepare_connectivity_operation, security_group_service,
              key_pair_service, tag_service, storage_service, network_service, vm_service,
              azure_models_parser, commands_results_parser, deployed_app_ports_operation, autoload_operation):
        self.azure_shell = AzureShell()
        self.logger = mock.MagicMock()
        self.group_name = "test group name"
        self.vm_name = "test VM name"

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_deploy_azure_vm(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                             cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and deploy_azure_vm_operation.deploy method"""
        # mock Cloudshell Session
        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager

        command_context = mock.MagicMock()
        cancellation_context = mock.MagicMock()
        deploy_action = mock.MagicMock(spec=DeployApp)
        deploy_action.actionId = '633698de-a142-439b-a4c6-b633729126a4'
        azure_vm_deployment_model = mock.MagicMock()
        cloud_provider_model = mock.MagicMock()
        reservation = mock.MagicMock()
        self.azure_shell.model_parser.convert_to_deploy_azure_vm_resource_model.return_value = azure_vm_deployment_model
        self.azure_shell.model_parser.convert_to_cloud_provider_resource_model.return_value = cloud_provider_model
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = reservation

        # Act
        self.azure_shell.deploy_azure_vm(command_context=command_context,
                                         actions=[deploy_action],
                                         cancellation_context=cancellation_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)
        self.azure_shell.deploy_azure_vm_operation.deploy_from_marketplace.assert_called_once_with(
            deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            reservation=reservation,
            network_actions=[],
            network_client=azure_clients_manager.network_client,
            compute_client=azure_clients_manager.compute_client,
            storage_client=azure_clients_manager.storage_client,
            cancellation_context=cancellation_context,
            logger=self.logger,
            cloudshell_session=cloudshell_session)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_deploy_vm_from_custom_image(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                                         cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and deploy_azure_vm_operation.deploy_from_custom_image method"""
        # mock Cloudshell Session
        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager

        command_context = mock.MagicMock()
        cancellation_context = mock.MagicMock()
        deploy_action = mock.MagicMock(spec=DeployApp)
        deploy_action.actionId = '633698de-a142-439b-a4c6-b633729126a4'
        azure_vm_deployment_model = mock.MagicMock()
        cloud_provider_model = mock.MagicMock()
        reservation = mock.MagicMock()
        self.azure_shell.model_parser.convert_to_deploy_azure_vm_from_custom_image_resource_model.return_value = azure_vm_deployment_model
        self.azure_shell.model_parser.convert_to_cloud_provider_resource_model.return_value = cloud_provider_model
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = reservation

        # Act
        self.azure_shell.deploy_vm_from_custom_image(command_context=command_context,
                                                     actions=[deploy_action],
                                                     cancellation_context=cancellation_context)

        # Verify

        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.deploy_azure_vm_operation.deploy_from_custom_image.assert_called_once_with(
            deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            reservation=reservation,
            network_actions=[],
            network_client=azure_clients_manager.network_client,
            compute_client=azure_clients_manager.compute_client,
            storage_client=azure_clients_manager.storage_client,
            cancellation_context=cancellation_context,
            logger=self.logger,
            cloudshell_session=cloudshell_session)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.jsonpickle")
    @mock.patch("cloudshell.cp.azure.azure_shell.DeployDataHolder")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_prepare_connectivity(self, error_handling_class, logging_context_class,
                                  azure_clients_manager_class, deploy_data_holder_class, jsonpickle,
                                  cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and prepare_connectivity_operation"""
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager
        # mock Resource Group name
        reservation = mock.MagicMock()
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = reservation

        cloud_provider_model = mock.MagicMock()
        self.azure_shell.model_parser.convert_to_cloud_provider_resource_model.return_value = cloud_provider_model
        deploy_data_holder = mock.MagicMock()
        deploy_data_holder_class.return_value = deploy_data_holder
        context = mock.MagicMock()
        actions = [mock.MagicMock()]
        cancellation_context = mock.MagicMock()
        prepare_connectivity_result = [mock.MagicMock()]
        self.azure_shell.prepare_connectivity_operation.prepare_connectivity.return_value = prepare_connectivity_result

        # Act
        self.azure_shell.prepare_connectivity(context=context,
                                              actions=actions,
                                              cancellation_context=cancellation_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)
        self.azure_shell.prepare_connectivity_operation.prepare_connectivity.assert_called_once_with(
            reservation=reservation,
            cloud_provider_model=cloud_provider_model,
            storage_client=azure_clients_manager.storage_client,
            resource_client=azure_clients_manager.resource_client,
            network_client=azure_clients_manager.network_client,
            logger=self.logger,
            actions=actions,
            cancellation_context=cancellation_context)

    @mock.patch("cloudshell.cp.azure.azure_shell.jsonpickle")
    @mock.patch("cloudshell.cp.azure.azure_shell.DeployDataHolder")
    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_cleanup_connectivity(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                                  cloudshell_session_context_class, deploy_data_holder_class, jsonpickle):
        """Check that method uses ErrorHandlingContext and delete_azure_vm_operation"""
        # mock Cloudshell Session
        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager

        deploy_data_holder = mock.MagicMock()
        deploy_data_holder_class.return_value = deploy_data_holder
        request = mock.MagicMock()

        command_context = mock.MagicMock(reservation=mock.MagicMock(reservation_id=self.group_name))
        cloud_provider_model = mock.MagicMock()
        self.azure_shell.model_parser.convert_to_cloud_provider_resource_model.return_value = cloud_provider_model

        # Act
        self.azure_shell.cleanup_connectivity(command_context=command_context, request=request)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.delete_azure_vm_operation.cleanup_connectivity.assert_called_once_with(
            network_client=azure_clients_manager.network_client,
            resource_client=azure_clients_manager.resource_client,
            cloud_provider_model=cloud_provider_model,
            resource_group_name=self.group_name,
            request=deploy_data_holder.driverRequest,
            logger=self.logger)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_delete_azure_vm(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                             cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and delete_azure_vm_operation.delete method"""

        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context

        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager
        # mock VM name
        data_holder = mock.MagicMock()
        vm_custom_param = mock.MagicMock()
        vm_custom_param.name = "resource_group"
        vm_custom_param.value = self.group_name
        data_holder.vmdetails.vmCustomParams = [vm_custom_param]
        self.azure_shell.model_parser.convert_app_resource_to_deployed_app.return_value = data_holder
        # mock Resource Group name
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = mock.MagicMock(
            reservation_id=self.group_name)

        command_context = mock.MagicMock(remote_endpoints=[mock.MagicMock(fullname=self.vm_name)])
        command_context.remote_reservation = mock.Mock()
        command_context.remote_reservation.reservation_id = self.group_name

        # Act
        self.azure_shell.delete_azure_vm(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.delete_azure_vm_operation.delete.assert_called_once_with(
            compute_client=azure_clients_manager.compute_client,
            network_client=azure_clients_manager.network_client,
            storage_client=azure_clients_manager.storage_client,
            group_name=self.group_name,
            vm_name=self.vm_name,
            logger=self.logger,
            cloudshell_session=cloudshell_session)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_power_on_vm(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                         cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and power_vm_operation.power_on method"""
        # mock Cloudshell Session
        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager
        # mock VM name
        data_holder = mock.MagicMock()
        data_holder.name = self.vm_name
        self.azure_shell.model_parser.convert_app_resource_to_deployed_app.return_value = data_holder
        # mock Resource Group name
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = mock.MagicMock(
            reservation_id=self.group_name)

        command_context = mock.MagicMock()
        resource_full_name = command_context.remote_endpoints[0].fullname

        # Act
        self.azure_shell.power_on_vm(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.power_vm_operation.power_on.assert_called_once_with(
            compute_client=azure_clients_manager.compute_client,
            resource_group_name=self.group_name,
            resource_full_name=resource_full_name,
            data_holder=data_holder,
            cloudshell_session=cloudshell_session)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_power_off_vm(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                          cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and power_vm_operation.power_off method"""
        # mock Cloudshell Session
        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager
        # mock VM name
        data_holder = mock.MagicMock()
        data_holder.name = self.vm_name
        self.azure_shell.model_parser.convert_app_resource_to_deployed_app.return_value = data_holder
        # mock Resource Group name
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = mock.MagicMock(
            reservation_id=self.group_name)

        command_context = mock.MagicMock()

        # Act
        self.azure_shell.power_off_vm(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.power_vm_operation.power_off.assert_called_once_with(
            compute_client=azure_clients_manager.compute_client,
            resource_group_name=self.group_name,
            vm_name=self.vm_name)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_refresh_ip(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                        cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and refresh_ip_operation.refresh_ip method"""
        # mock Cloudshell Session
        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager
        # mock VM name
        data_holder = mock.MagicMock()
        data_holder.name = self.vm_name
        self.azure_shell.model_parser.convert_app_resource_to_deployed_app.return_value = data_holder
        # mock Resource Group name
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = mock.MagicMock(
            reservation_id=self.group_name)

        command_context = mock.MagicMock()
        private_ip = mock.MagicMock()
        public_ip = mock.MagicMock()
        resource_fullname = mock.MagicMock()

        self.azure_shell.model_parser.get_private_ip_from_connected_resource_details.return_value = private_ip
        self.azure_shell.model_parser.get_public_ip_from_connected_resource_details.return_value = public_ip
        self.azure_shell.model_parser.get_connected_resource_fullname.return_value = resource_fullname

        # Act
        self.azure_shell.refresh_ip(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.refresh_ip_operation.refresh_ip.assert_called_once_with(
            cloudshell_session=cloudshell_session,
            compute_client=azure_clients_manager.compute_client,
            network_client=azure_clients_manager.network_client,
            resource_group_name=self.group_name,
            vm_name=self.vm_name,
            private_ip_on_resource=private_ip,
            public_ip_on_resource=public_ip,
            resource_fullname=resource_fullname,
            logger=self.logger)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_get_application_ports(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                                   cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and get_formated_deployed_app_ports method"""
        # mock Cloudshell Session
        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        vm_nsg = mock.MagicMock()
        mock_rules = [SecurityRule(name='rule_2500', source_address_prefix='srcPrefix', source_port_range='10-20',
                                   destination_address_prefix='destPrefix', destination_port_range='10-20',
                                   protocol='tcp', direction='bi', access='all')]
        vm_nsg.security_rules = mock_rules

        azure_clients_manager.network_client.network_security_groups.get.return_value = vm_nsg
        azure_clients_manager_class.return_value = azure_clients_manager

        resource = mock.MagicMock()
        reservation = mock.MagicMock()
        reservation.reservation_id = 'ghi'
        resource.fullname = 'abc'
        command_context = mock.MagicMock(remote_endpoints=[resource])
        data_holder = mock.MagicMock()
        self.azure_shell.model_parser.convert_app_resource_to_deployed_app.return_value = data_holder
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = reservation
        self.azure_shell.model_parser.get_allow_all_storage_traffic_from_connected_resource_details.return_value \
            = True

        expected_output = "App Name: abc\n" \
                          "Allow Sandbox Traffic: True\n" \
                          "Ports: 10-20, Protocol: tcp, Destination: destPrefix"

        # Act
        actual_output = self.azure_shell.get_application_ports(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.assertTrue(expected_output == actual_output)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_get_access_key(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                            cloudshell_session_context_class):
        # mock Cloudshell Session
        cloudshell_session = mock.MagicMock()
        cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        cloudshell_session_context_class.return_value = cloudshell_session_context
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager
        # mock Resource Group name
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = mock.MagicMock(
            reservation_id=self.group_name)
        # mock command context
        resource = mock.MagicMock()
        command_context = mock.MagicMock(remote_endpoints=[resource])

        # Act
        self.azure_shell.get_access_key(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.model_parser.convert_to_cloud_provider_resource_model.assert_called_once_with(
            resource=command_context.resource,
            cloudshell_session=cloudshell_session)

    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_get_inventory(self, error_handling_class, logging_context_class, cloudshell_session_context_class):
        """Check that method uses ErrorHandlingContext and Autoload operation"""
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling

        command_context = mock.MagicMock()
        cloud_provider_model = mock.MagicMock()
        self.azure_shell.autoload_operation.get_inventory.return_value = expected_res = mock.MagicMock()
        self.azure_shell.model_parser.convert_to_cloud_provider_resource_model.return_value = cloud_provider_model

        # Act
        res = self.azure_shell.get_inventory(command_context=command_context)

        # Verify
        self.azure_shell.autoload_operation.get_inventory.assert_called_once_with(
            cloud_provider_model=cloud_provider_model,
            logger=self.logger)

        self.assertEqual(res, expected_res)

        # @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
        # @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
        # @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
        # @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
        # def test_set_app_security_groups(self, error_handling_class, logging_context_class,
        #                                  cloudshell_session_context_class, azure_clients_manager_class):
        #     """ Can create app security groups """
        #     # region Configuration of contexts used by AzureShell
        #     # mock Cloudshell Session
        #     cloudshell_session = mock.MagicMock()
        #     cloudshell_session_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=cloudshell_session))
        #     cloudshell_session_context_class.return_value = cloudshell_session_context
        #     # mock LoggingSessionContext and ErrorHandlingContext
        #     logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        #     logging_context_class.return_value = logging_context
        #     error_handling = mock.MagicMock()
        #     error_handling_class.return_value = error_handling
        #     # mock AzureClientManager
        #     azure_clients_manager = mock.MagicMock()
        #     azure_clients_manager_class.return_value = azure_clients_manager
        #     # endregion
        #
        #     command_context = mock.MagicMock()
        #     request = mock.MagicMock()
        #     self.azure_shell.model_parser.convert_to_app_security_group_models.return_value = [AppSecurityGroupModel()]
        #
        #     result = self.azure_shell.set_app_security_groups(command_context, request)
        #     # self.azure_shell.set_app_security_groups_operation.set_apps_security_groups.assert_called_once_with(self.logger)
        #     return 1==1
