from unittest import TestCase

from cloudshell.cp.azure.domain.services.parsers.azure_resource_id_parser import AzureResourceIdParser


class TestAzureResourceIdParser(TestCase):
    def setUp(self):
        self.tested_class = AzureResourceIdParser

    def test_convert_app_resource_to_deployed_app(self):
        """Check that method will retrieve name from the Azure resource Id string"""
        resource_name = "testresourcename"
        resource_id = ("/subscriptions/b9f0be86-aaf9-4030-a6e3-e89062c6d67d/resourceGroups/testgroup/"
                       "providers/Microsoft.Compute/virtualMachines/{}".format(resource_name))

        # Act
        result = self.tested_class.get_name_from_resource_id(resource_id)

        # Verify
        self.assertEqual(result, resource_name)

    def test_convert_app_resource_to_deployed_app(self):
        """Check that method will retrieve resource group name from the Azure resource Id string"""
        resource_group_name = "testgroup"
        resource_id = ("/subscriptions/b9f0be86-aaf9-4030-a6e3-e89062c6d67d/resourceGroups/{}/"
                       "providers/Microsoft.Compute/virtualMachines/testresourcename".format(resource_group_name))

        # Act
        result = self.tested_class.get_resource_group_name(resource_id=resource_id)

        # Verify
        self.assertEqual(result, resource_group_name)
