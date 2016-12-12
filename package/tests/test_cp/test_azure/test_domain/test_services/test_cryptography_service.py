from unittest import TestCase

from cloudshell.cp.azure.domain.services.cryptography_service import CryptographyService


class TestCryptographyService(TestCase):
    def setUp(self):
        self.cryptography_service = CryptographyService()

    def test_encrypt(self):
        # Arrange
        plain_text = "password"
        self.crypto_service = CryptographyService()

        # Act
        encrypted_text = self.crypto_service.encrypt(plain_text)

        # Verify
        # self.assertEqual(plain_text, result)
        # no check - just verify there is no exception
