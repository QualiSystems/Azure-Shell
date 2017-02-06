from unittest import TestCase

from cloudshell.cp.azure.common.parsers.azure_resource_id_parser import AzureResourceIdParser


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
