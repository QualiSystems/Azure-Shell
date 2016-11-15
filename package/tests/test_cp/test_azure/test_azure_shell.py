from unittest import TestCase

import mock

from cloudshell.cp.azure.azure_shell import AzureShell


class TestAzureShell(TestCase):

    @mock.patch("cloudshell.cp.azure.azure_shell.CommandResultsParser")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureModelsParser")
    @mock.patch("cloudshell.cp.azure.azure_shell.VirtualMachineService")
    @mock.patch("cloudshell.cp.azure.azure_shell.NetworkService")
    @mock.patch("cloudshell.cp.azure.azure_shell.StorageService")
    @mock.patch("cloudshell.cp.azure.azure_shell.TagService")
    @mock.patch("cloudshell.cp.azure.azure_shell.KeyPairService")
    @mock.patch("cloudshell.cp.azure.azure_shell.SecurityGroupService")
    @mock.patch("cloudshell.cp.azure.azure_shell.PrepareConnectivityOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.DeployAzureVMOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.PowerAzureVMOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.RefreshIPOperation")
    @mock.patch("cloudshell.cp.azure.azure_shell.DeleteAzureVMOperation")
    def setUp(self, delete_azure_vm_operation, refresh_ip_operation, power_azure_vm_operation,
              deploy_azure_vm_operation, prepare_connectivity_operation, security_group_service,
              key_pair_service, tag_service, storage_service, network_service, vm_service,
              azure_models_parser, commands_results_parser):

        self.azure_shell = AzureShell()
        self.logger = mock.MagicMock()
        self.group_name = "test group name"
        self.vm_name = "test VM name"

    @mock.patch("cloudshell.cp.azure.azure_shell.ValidatorsFactoryContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.CloudShellSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_deploy_azure_vm(self, error_handling_class, logging_context_class, azure_clients_manager_class,
                             cloudshell_session_context_class, validators_factory_context_class):
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
        # mock ValidatorsFactoryContext
        validator_factory = mock.MagicMock()
        validator_factory_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=validator_factory))
        validators_factory_context_class.return_value = validator_factory_context

        command_context = mock.MagicMock()
        deployment_request = mock.MagicMock()
        azure_vm_deployment_model = mock.MagicMock()
        cloud_provider_model = mock.MagicMock()
        reservation = mock.MagicMock()
        self.azure_shell.model_parser.convert_to_deployment_resource_model.return_value = azure_vm_deployment_model
        self.azure_shell.model_parser.convert_to_cloud_provider_resource_model.return_value = cloud_provider_model
        self.azure_shell.model_parser.convert_to_reservation_model.return_value = reservation

        # Act
        self.azure_shell.deploy_azure_vm(command_context=command_context,
                                         deployment_request=deployment_request)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)
        self.azure_shell.deploy_azure_vm_operation.deploy.assert_called_once_with(
            azure_vm_deployment_model=azure_vm_deployment_model,
            cloud_provider_model=cloud_provider_model,
            reservation=reservation,
            network_client=azure_clients_manager.network_client,
            compute_client=azure_clients_manager.compute_client,
            storage_client=azure_clients_manager.storage_client,
            validator_factory=validator_factory)

    @mock.patch("cloudshell.cp.azure.azure_shell.jsonpickle")
    @mock.patch("cloudshell.cp.azure.azure_shell.DeployDataHolder")
    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_prepare_connectivity(self, error_handling_class, logging_context_class,
                                  azure_clients_manager_class, deploy_data_holder_class, jsonpickle):
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
        request = mock.MagicMock()
        prepare_connectivity_result = mock.MagicMock()
        self.azure_shell.prepare_connectivity_operation.prepare_connectivity.return_value = prepare_connectivity_result

        # Act
        self.azure_shell.prepare_connectivity(context=context, request=request)

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
            request=deploy_data_holder.driverRequest)

        self.azure_shell.command_result_parser.set_command_result.assert_called_once_with(
            {'driverResponse': {'actionResults': prepare_connectivity_result}})

    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_cleanup_connectivity(self, error_handling_class, logging_context_class,
                                  azure_clients_manager_class):
        """Check that method uses ErrorHandlingContext and delete_azure_vm_operation"""
        # mock LoggingSessionContext and ErrorHandlingContext
        logging_context = mock.MagicMock(__enter__=mock.MagicMock(return_value=self.logger))
        logging_context_class.return_value = logging_context
        error_handling = mock.MagicMock()
        error_handling_class.return_value = error_handling
        # mock Azure clients
        azure_clients_manager = mock.MagicMock()
        azure_clients_manager_class.return_value = azure_clients_manager

        command_context = mock.MagicMock(reservation=mock.MagicMock(reservation_id=self.group_name))
        cloud_provider_model = mock.MagicMock()
        self.azure_shell.model_parser.convert_to_cloud_provider_resource_model.return_value = cloud_provider_model

        # Act
        self.azure_shell.cleanup_connectivity(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.delete_azure_vm_operation.cleanup_connectivity.assert_called_once_with(
            network_client=azure_clients_manager.network_client,
            resource_client=azure_clients_manager.resource_client,
            cloud_provider_model=cloud_provider_model,
            resource_group_name=self.group_name,
            logger=self.logger)

    @mock.patch("cloudshell.cp.azure.azure_shell.AzureClientsManager")
    @mock.patch("cloudshell.cp.azure.azure_shell.LoggingSessionContext")
    @mock.patch("cloudshell.cp.azure.azure_shell.ErrorHandlingContext")
    def test_delete_azure_vm(self, error_handling_class, logging_context_class, azure_clients_manager_class):
        """Check that method uses ErrorHandlingContext and delete_azure_vm_operation.delete method"""
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

        # Act
        self.azure_shell.delete_azure_vm(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.delete_azure_vm_operation.delete.assert_called_once_with(
            compute_client=azure_clients_manager.compute_client,
            network_client=azure_clients_manager.network_client,
            group_name=self.group_name,
            vm_name=self.vm_name,
            logger=self.logger)

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

        # Act
        self.azure_shell.power_on_vm(command_context=command_context)

        # Verify
        error_handling.__enter__.assert_called_once_with()
        error_handling_class.assert_called_once_with(self.logger)

        self.azure_shell.power_vm_operation.power_on.assert_called_once_with(
            compute_client=azure_clients_manager.compute_client,
            resource_group_name=self.group_name,
            vm_name=self.vm_name)

        cloudshell_session.SetResourceLiveStatus.assert_called_once_with(
            command_context.remote_endpoints[0].fullname, "Online", "Active")

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

        cloudshell_session.SetResourceLiveStatus.assert_called_once_with(
            command_context.remote_endpoints[0].fullname, "Offline", "Powered Off")

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
            resource_fullname=resource_fullname)
