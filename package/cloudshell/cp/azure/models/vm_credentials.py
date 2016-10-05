class VMCredentials(object):
    def __init__(self, admin_username, admin_password=None, ssh_key=None):
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.ssh_key = ssh_key
