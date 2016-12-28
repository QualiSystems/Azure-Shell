from unittest import TestCase

from azure.mgmt.storage.models import StorageAccount

from cloudshell.cp.azure.common.validtors.validator_factory import ValidatorProvider


class TestValidators(TestCase):
    def setUp(self):
        pass

    def test_validator_not_found_throw_exception(self):
        # Arrange
        validator_factory = ValidatorProvider()

        # Act
        self.assertRaises(Exception,
                          validator_factory.try_validate,
                          StorageAccount,
                          None)
