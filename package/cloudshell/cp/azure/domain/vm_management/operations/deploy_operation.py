from azure.mgmt.compute import VirtualMachine, OSProfile, HardwareProfile, NetworkProfile, StorageProfile, OSDisk, \
    VirtualHardDisk, ImageReference, VirtualMachineSizeTypes, NetworkInterfaceReference, CachingTypes, \
    DiskCreateOptionTypes

from cloudshell.cp.azure.models.deploy_result_model import DeployResult


class DeployAzureVMOperation(object):
    """

    """

    def __init__(self):
        """

        """

    def deploy(self, logger, compute_client, azure_vm_deployment_model):
        """

        :param azure_vm_deployment_model:
        :param compute_client:
        :param logging.Logger logger:
        :return: DeployResult result
        """

        deploy_data = compute_client.virtual_machines.create_or_update(
            azure_vm_deployment_model.group_name,
            azure_vm_deployment_model.vm_name,
            VirtualMachine(
                location='TBD',
                os_profile=OSProfile(
                    computer_name='TBD',
                    admin_username='TBD',
                    admin_password='TBD'
                ),
                hardware_profile=HardwareProfile(
                    vm_size=VirtualMachineSizeTypes.basic_a0
                ),
                network_profile=NetworkProfile(
                    network_interfaces=[
                        NetworkInterfaceReference(
                            id='TBD'
                        ),
                    ]
                ),
                storage_profile=StorageProfile(
                    os_disk=OSDisk(
                        caching=CachingTypes.none,
                        create_option=DiskCreateOptionTypes.from_image,
                        name='TBD',
                        vhd=VirtualHardDisk(
                            uri='TBD',  # the VM name
                            )
                        )
                    ),
                    image_reference=ImageReference(
                        publisher=azure_vm_deployment_model.image_publisher,
                        offer=azure_vm_deployment_model.image_offer,
                        sku=azure_vm_deployment_model.image_sku,
                        version='TBD'
                    )
                )
            )
        )

        return DeployResult()
