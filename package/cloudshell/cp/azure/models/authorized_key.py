class AuthorizedKey(object):
    def __init__(self, path_to_key, key_data):
        """
        :param path_to_key: (str) path for authorized public keys file on the Azure VM
        :param key_data: (str) SSH public key
        """
        self.path_to_key = path_to_key
        self.key_data = key_data

