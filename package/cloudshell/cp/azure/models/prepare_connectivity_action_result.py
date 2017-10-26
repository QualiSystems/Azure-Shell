class PrepareNetworkActionResult(object):
    def __init__(self):
        self.actionId = ''
        self.success = True
        self.infoMessage = ''
        self.errorMessage = ''
        self.type = 'PrepareNetwork'
        self.access_key = ''
        self.secret_key = ''


class PrepareSubnetActionResult(object):
    def __init__(self, action_id=''):
        self.actionId = action_id
        self.success = True
        self.infoMessage = ''
        self.errorMessage = ''
        self.subnetId = ''
