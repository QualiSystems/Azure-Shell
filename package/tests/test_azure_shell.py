from unittest import TestCase
from mock import Mock, patch, MagicMock
from cloudshell.cp.azure.azure_shell import AzureShell
from cloudshell.cp.azure.models.deploy_azure_vm_resource_model import DeployAzureVMResourceModel
from cloudshell.cp.azure.models.deploy_result_model import DeployResult


class TestAzureShell(TestCase):
    def setUp(self):
        self.azure_shell = AzureShell()

    def test_deploying_azure_vm_returns_deploy_result(self):
        deploymock = DeployAzureVMResourceModel()
        deploymock.app_name = 'my instance name'

        result = DeployResult()

        self.azure_shell.model_parser.convert_to_deployment_resource_model = Mock(return_value=deploymock)
        self.azure_shell.deploy_azure_vm = Mock(return_value=result)
