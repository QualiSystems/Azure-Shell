from unittest import TestCase

from cloudshell.shell.core.driver_context import ResourceCommandContext
from mock import Mock

from drivers.deployment_drivers.azure_vm.driver import DeployAzureVM


class TestDeployAzureVM(TestCase):
    def setUp(self):
        self.deploy_azure_vm = DeployAzureVM()

    def test_deploy_azure_vm(self):
        self.deploy_azure_vm.Deploy(ResourceCommandContext(Mock(), Mock(), Mock(), Mock()))
