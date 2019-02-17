import logging

from azure.mgmt.compute.compute_management_client import ComputeManagementClient
from azure.mgmt.network.models import NetworkInterface
from cloudshell.shell.core.driver_context import CancellationContext
from typing import Dict, List

from cloudshell.cp.azure.models.azure_cloud_provider_resource_model import AzureCloudProviderResourceModel
from cloudshell.cp.azure.models.deploy_azure_vm_resource_models import DeployAzureVMFromSnapshotResourceModel
from cloudshell.cp.azure.models.image_data import SnapshotDataModel


class CreateVmFromSnapshotRequest(object):
    def __init__(self, compute_client, deployment_model, cloud_provider_model, data, cancellation_context, logger):
        """Create VM from snapshot

        :param DeployAzureVMFromSnapshotResourceModel deployment_model:
        :param AzureCloudProviderResourceModel cloud_provider_model:
        :param ComputeManagementClient compute_client:
        :param DeployDataModel data:
        :param CancellationContext cancellation_context:
        :param logging.Logger logger:
        """
        self.logger = logger                                                        # type: logging.Logger
        self.compute_client = compute_client                                        # type: ComputeManagementClient
        self.disk_type = deployment_model.disk_type                                 # type: str
        self.sandbox_resource_group = data.group_name                               # type: str
        self.nics = data.nics                                                       # type: List[NetworkInterface]
        self.region = cloud_provider_model.region                                   # type: str
        self.vm_name = data.vm_name                                                 # type: str
        self.tags = data.tags                                                       # type: Dict[str, str]
        self.vm_size = data.vm_size                                                 # type: str
        self.disk_size = deployment_model.disk_size                                 # type: str
        self.snapshot_model = data.image_model                                      # type: SnapshotDataModel
        self.private_static_ip = deployment_model.private_static_ip                 # type: str
        self.cancellation_context = cancellation_context                            # type: CancellationContext
