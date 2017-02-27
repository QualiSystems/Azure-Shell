from unittest import TestCase

import mock

from cloudshell.cp.azure.domain.services.name_provider import NameProviderService


class TestNameProviderService(TestCase):
    def setUp(self):
        self.name_provider_service = NameProviderService()

    def test_generate_name_auto_postfix(self):
        """Check that method will generate name based on the given one with the given max length"""
        test_name = "sometestname"
        test_length = 30
        # Act
        result = self.name_provider_service.generate_name(name=test_name, max_length=test_length)

        # Verify
        self.assertLess(len(result), test_length)
        self.assertTrue(result.startswith(test_name + "-"))

    def test_generate_name_specific_postfix_short_length(self):
        """Check that method will generate name based on the given one with the given max length"""
        test_name = "-some-test-name"
        test_postfix = "xxxxxxxx"
        test_length = 15
        # Act
        result = self.name_provider_service.generate_name(name=test_name, max_length=test_length, postfix=test_postfix)

        # Verify
        self.assertEquals(len(result), test_length)
        self.assertEquals(result, "some-t-xxxxxxxx")

    def test_generate_name_with_long_base_name(self):
        """Check that method will always generate unique names"""
        test_name = "someveryveryveryveryveryveryveryveryveryveryveryverylongtestname"

        # Act
        name1 = self.name_provider_service.generate_name(test_name)
        name2 = self.name_provider_service.generate_name(test_name)

        # Verify
        self.assertNotEqual(name1, name2)

    def test_generate_short_unique_string(self):
        """Check that method will always generate unique names"""
        # Act
        uuid1 = self.name_provider_service.generate_short_unique_string()
        uuid2 = self.name_provider_service.generate_short_unique_string()

        # Verify
        self.assertNotEqual(uuid1, uuid2)
        self.assertEquals(len(uuid1), 8)
        self.assertEquals(len(uuid2), 8)

    def test_normalize_resource_name(self):
        # Assert
        test_name = "Some Test Name"

        # Act
        result = self.name_provider_service.normalize_name(name=test_name)

        # Verify
        self.assertEquals(result, "some-test-name")
