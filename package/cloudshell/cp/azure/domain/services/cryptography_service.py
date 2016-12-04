import base64
import os

from Crypto import Random

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5, AES
from cloudshell.core.cryptography.rsa_service import RsaService


class CryptographyDto(object):
    def __init__(self):
        """
        """
        self.encrypted_input = ""
        self.encrypted_asymmetric_key = ""


class CryptographyService(object):
    def __init__(self):
        """
        """
        self.public_key_text = ""

    def encrypt(self, input):
        self.public_key_text = RsaService.read_public_key()
        public_key = RSA.importKey(self.public_key_text)
        secret_key = base64.b64encode(os.urandom(16))
        rsa_cipher = PKCS1_v1_5.new(public_key)

        encrypted_input = AESCipher(secret_key).encrypt(input)
        encrypted_secret_key = base64.b64encode(rsa_cipher.encrypt(secret_key))

        cryptography_dto = CryptographyDto()
        cryptography_dto.encrypted_input = encrypted_input
        cryptography_dto.encrypted_asymmetric_key = encrypted_secret_key

        return cryptography_dto

        # encrypted_bytes = cipher.encrypt(input)
        # return base64.b64encode(encrypted_bytes)


class AESCipher:
    def __init__(self, key):
        self.key = base64.b64decode(key)

    def encrypt(self, raw):
        BS = 16
        pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        raw = pad(raw)

        iv = Random.new().read(BS)

        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        res = iv + cipher.encrypt(raw)
        return base64.b64encode(res)

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        BS = 16
        iv = enc[:BS]
        unpad = lambda s: s[:-ord(s[-1])]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc[BS:]))
