from unittest import TestCase
from mock import Mock

from cloudshell.cp.azure.domain.services.cryptography_service import CryptographyService


class TestCryptographyService(TestCase):
    def setUp(self):
        self.crypto_service = CryptographyService()
        self.crypto_service.rsa_service = Mock()

    def test_encrypt(self):
        # Arrange
        plain_text = "password"

        encrypted_secret_key = Mock()
        self.crypto_service.rsa_service.encrypt = Mock(return_value=encrypted_secret_key)

        # Act
        crypto_dto = self.crypto_service.encrypt(plain_text)

        # Verify
        self.crypto_service.rsa_service.encrypt.assert_called_once()
        self.assertEquals(crypto_dto.encrypted_asymmetric_key, encrypted_secret_key)
        self.assertNotEquals(crypto_dto.encrypted_input, plain_text)
        self.assertTrue(crypto_dto.encrypted_input)

