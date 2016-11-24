from Crypto.PublicKey import RSA


class CryptographyService(object):
    def __init__(self):
        """
        """
        self.public_key = """-----BEGIN PUBLIC KEY-----
                                MIGeMA0GCSqGSIb3DQEBAQUAA4GMADCBiAKBgFWgDE+P4ScaSfM0RP95mgftt6hz
                                /ISyF6kqeAgBjCiCMGnJEdh9UTKIsgWSgIOCz7tD3tLEa2KwV09dm/mvU1t+XJRr
                                29GPexCrZm/2d2nE45iscLVS9hyUNPAU5LByrNMQlJTDjWvlLpubQRyH+Hlq55CT
                                Pzc4Vte+G7wQ+FVVAgMBAAE=
                                -----END PUBLIC KEY-----"""

        self.private_key = """-----BEGIN RSA PRIVATE KEY-----
                                MIICWgIBAAKBgFWgDE+P4ScaSfM0RP95mgftt6hz/ISyF6kqeAgBjCiCMGnJEdh9
                                UTKIsgWSgIOCz7tD3tLEa2KwV09dm/mvU1t+XJRr29GPexCrZm/2d2nE45iscLVS
                                9hyUNPAU5LByrNMQlJTDjWvlLpubQRyH+Hlq55CTPzc4Vte+G7wQ+FVVAgMBAAEC
                                gYAGqyBKUfpHAVUhC8ET5HSKiYj0JZRVAUm2cwhGF1jDDuCWXIJ3Scs5FExJAs/f
                                biCfhPmlkIaMeQ9Trwamu3DSaAyvrOqNrM1w2yi/wLCRDXg6gKjqz0gPg1RQUvvo
                                LUDh1ixLpfe2Di9AXGh5nivos1Fato/UUkJRd0eEKFebQQJBAKoFKfz0w351gxD3
                                pZTzmpFspqXhHR7fPSTS2Zus7GL7BpBVQjkpx2sIaDUEOPecf3kJ0cc/lKKibbgF
                                E2iM/ncCQQCA7Rjl9pLp8Zud9qtphiEnw5YYC2hxvQ1oxWpe7JKmHJP4t5t0jZKG
                                uSH2Pv6EC2GB0DOQ4wBfmowM3E37SkGTAkAEG1HTUVozgMUksMaoHWY7YwN3eEOK
                                zlucuxcUgo3HKkcTT2vlE5REipRxy2NQ38/YbZtKk8eUUhYSXtUELnurAkAD5ymZ
                                zJ0l9+p+HbmSuDzIt2MT10SSLOb7BP7zYLYP0U2peeV64c5Nxc0BZ2bNGIsbIvJs
                                sHKScltLCGBT+yuBAkBurazauqbzExl8Y9iNYU+xaf2zTqsYNYZZvm2xysYNt/uP
                                hSnHc+6eW4YeUVy8NUjyhjBXO4psjGturnSZcVH3
                                -----END RSA PRIVATE KEY-----"""

    def encrypt(self, input):
        public_key = RSA.importKey(self.public_key)
        return public_key.encrypt(input, 32)[0]

    def decrypt(self, input):
        private_key = RSA.importKey(self.private_key)
        return private_key.decrypt(input)
