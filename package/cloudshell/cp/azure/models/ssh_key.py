class SSHKey(object):
    def __init__(self, path_to_key, key_data):
        self.path_to_key = path_to_key
        self.key_data = key_data

class AzureSSHKey(object):
    def __init__(self, private_key, public_key):
        self.private_key = private_key
        self.public_key = public_key
