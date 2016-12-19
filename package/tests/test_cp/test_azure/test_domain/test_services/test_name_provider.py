from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.services.name_provider import NameProviderService


class TestNameProviderService(TestCase):
    def setUp(self):
        self.name_provider_service = NameProviderService()

    def test_generate_name(self):
        """Check that method will generate name based on the given one with the given length"""
        test_name = "sometestname"
        test_length = 30
        # Act
        result = self.name_provider_service.generate_name(name=test_name, length=test_length)

        # Verify
        self.assertEqual(len(result), test_length)
        self.assertIn(test_name[:8], result)

    def test_generate_name_with_long_base_name(self):
        """Check that method will always generate unique names"""
        test_name = "someveryveryveryveryveryveryveryveryveryveryveryverylongtestname"

        # Act
        name1 = self.name_provider_service.generate_name(test_name)
        name2 = self.name_provider_service.generate_name(test_name)

        # Verify
        self.assertNotEqual(name1, name2)
