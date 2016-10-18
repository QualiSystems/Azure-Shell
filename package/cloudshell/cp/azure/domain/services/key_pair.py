from Crypto.PublicKey import RSA

from cloudshell.cp.azure.models.ssh_key import SSHKey


class KeyPairService(object):
    def generate_key_pair(self, key_length=2048):
        """Generate SSH key pair model

        :param key_length: (int) SSH key length
        :return: cloudshell.cp.azure.models.ssh_key.SSHKey instance
        """
        key = RSA.generate(key_length)
        pubkey = key.publickey()

        private_key = key.exportKey('PEM')
        public_key = pubkey.exportKey('OpenSSH')

        return SSHKey(private_key=private_key, public_key=public_key)
