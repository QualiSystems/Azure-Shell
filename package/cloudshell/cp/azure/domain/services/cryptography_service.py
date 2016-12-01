import base64

from Crypto.PublicKey import RSA
from cloudshell.core.cryptography.rsa_service import RsaService


class CryptographyService(object):
    def __init__(self):
        """
        """
        self.public_key_text = ""

    def encrypt(self, input):
        self.public_key_text = RsaService.read_public_key()
        public_key = RSA.importKey(self.public_key_text)
        return base64.b64encode(public_key.encrypt(input, 32)[0])
