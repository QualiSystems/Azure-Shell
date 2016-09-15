import azure
from azure.mgmt.compute.models import OSProfile, HardwareProfile, VirtualMachineSizeTypes, NetworkProfile, \
    NetworkInterfaceReference, CachingTypes, DiskCreateOptionTypes, VirtualHardDisk, ImageReference, OSDisk
from azure.mgmt.network.models import NetworkInterfaceIPConfiguration, IPAllocationMethod, NetworkInterface
from azure.mgmt.storage.models import StorageAccountCreateParameters, SkuName


class VirtualMachineService(object):
    def __init__(self, compute_management_client, resource_management_client, storage_client, network_client):
        self.compute_management_client = compute_management_client
        self.resource_management_client = resource_management_client
        self.storage_client = storage_client
        self.network_client = network_client

    @staticmethod
    def create_vm(image_offer, image_publisher, image_sku, image_version, admin_password, admin_username,
                  compute_client, computer_name, group_name, nic_id, region, storage_name, vm_name):
        compute_client.virtual_machines.create_or_update(
            group_name,
            vm_name,
            azure.mgmt.compute.models.VirtualMachine(
                location=region,
                os_profile=OSProfile(
                    admin_username=admin_username,
                    admin_password=admin_password,
                    computer_name=computer_name,
                ),
                hardware_profile=HardwareProfile(
                    vm_size=VirtualMachineSizeTypes.basic_a0
                ),
                network_profile=NetworkProfile(
                    network_interfaces=[
                        NetworkInterfaceReference(
                            id=nic_id
                        ),
                    ],
                ),
                storage_profile=azure.mgmt.compute.models.StorageProfile(
                    os_disk=OSDisk(
                        caching=CachingTypes.none,
                        create_option=DiskCreateOptionTypes.from_image,
                        name=storage_name,
                        vhd=VirtualHardDisk(
                            uri='https://{0}.blob.core.windows.net/vhds/{1}.vhd'.format(
                                storage_name,
                                vm_name,  # the VM name
                            ),
                        ),
                    ),
                    image_reference=ImageReference(
                        publisher=image_publisher,
                        offer=image_offer,
                        sku=image_sku,
                        version=image_version
                    ),
                ),
            ),
        )

    def create_network(self, group_name, interface_name, ip_name, network_name, region, subnet_name):
        nic_id = self.create_network_interface(
            self.network_client,
            region,
            group_name,
            interface_name,
            network_name,
            subnet_name,
            ip_name,
        )
        return nic_id

    def create_storage_account(self, group_name, region, storage_account_name):
        storage_accounts_create = self.storage_client.storage_accounts.create(group_name, storage_account_name,
                                                                              StorageAccountCreateParameters(
                                                                                  sku=azure.mgmt.storage.models.Sku(
                                                                                      SkuName.standard_lrs),
                                                                                  kind=azure.mgmt.storage.models.Kind.storage.value,
                                                                                  location=region))
        storage_accounts_create.wait()  # async operation

    def create_network_interface(self, network_client, region, management_group_name, interface_name,
                                 network_name, subnet_name, ip_name):
        result = network_client.virtual_networks.create_or_update(
            management_group_name,
            network_name,
            azure.mgmt.network.models.VirtualNetwork(
                location=region,
                address_space=azure.mgmt.network.models.AddressSpace(
                    address_prefixes=[
                        '10.1.0.0/16',
                    ],
                ),
                subnets=[
                    azure.mgmt.network.models.Subnet(
                        name=subnet_name,
                        address_prefix='10.1.0.0/24',
                    ),
                ],
            ),
        )

        result.wait()

        subnet = network_client.subnets.get(management_group_name, network_name, subnet_name)

        result = network_client.public_ip_addresses.create_or_update(
            management_group_name,
            ip_name,
            azure.mgmt.network.models.PublicIPAddress(
                location=region,
                public_ip_allocation_method=azure.mgmt.network.models.IPAllocationMethod.dynamic,
                idle_timeout_in_minutes=4,
            ),
        )

        result.wait()

        public_ip_address = network_client.public_ip_addresses.get(management_group_name, ip_name)
        public_ip_id = public_ip_address.id

        result = network_client.network_interfaces.create_or_update(
            management_group_name,
            interface_name,
            NetworkInterface(
                location=region,
                ip_configurations=[
                    NetworkInterfaceIPConfiguration(
                        name='default',
                        private_ip_allocation_method=IPAllocationMethod.dynamic,
                        subnet=subnet,
                        public_ip_address=azure.mgmt.network.models.PublicIPAddress(
                            id=public_ip_id,
                        ),
                    ),
                ],
            ),
        )

        result.wait()

        network_interface = network_client.network_interfaces.get(
            management_group_name,
            interface_name,
        )

        return network_interface.id
