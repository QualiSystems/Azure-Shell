class AzureCloudProviderResourceModel(object):
    def __init__(self):
        self.azure_client_id = ''  # type: str
        self.azure_mgmt_network_d = ''  # type: str
        self.azure_mgmt_nsg_id = ''  # type: str
        self.azure_secret = ''  # type: str
        self.region = ''  # type: str
        self.vm_size = ''  # type: str
        self.keypairs_location = ''  # type: str
        self.networks_in_use = ''  # type: str
        self.azure_subscription_id = ''  # type: str
        self.azure_tenant = ''  # type: str
        self.storage_type = ''  # type: str
        self.management_group_name = ''  # type: str
        self.additional_mgmt_networks = ''  # type: str
