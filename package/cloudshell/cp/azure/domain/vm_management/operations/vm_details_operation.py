import traceback

from cloudshell.cp.core.models import VmDetailsData
from cloudshell.cp.azure.common.parsers.custom_param_extractor import VmCustomParamsExtractor


class VmDetailsOperation(object):
    def __init__(self, vm_service, vm_details_provider, vm_custom_params_extractor):
        """
        :type vm_service: cloudshell.cp.azure.domain.services.virtual_machine_service.VirtualMachineService
        :type vm_details_provider: cloudshell.cp.azure.domain.common.vm_details_provider.VmDetailsProvider
        :type vm_custom_params_extractor: VmCustomParamsExtractor
        """
        self.vm_service = vm_service
        self.vm_details_provider = vm_details_provider
        self.vm_custom_params_extractor = vm_custom_params_extractor

    def get_vm_details(self, compute_client, sandbox_id, requests, logger, network_client, model_parser, cancellation_context):
        """
        :param cancellation_context:
        :param model_parser:
        :param requests:
        :param network_client:
        :param compute_client: azure.mgmt.compute.ComputeManagementClient instance
        :param sandbox_id: sandbox/reservation id
        :param logging.Logger logger:
        :return: cloudshell.cp.azure.domain.common.vm_details_provider.VmDetails
        """

        results = []
        for request in requests:
            if cancellation_context.is_cancelled:
                break

            vm_name = request.deployedAppJson.name
            deployment_service = request.appRequestJson.deploymentService
            is_market_place = filter(lambda x: x.name == "Image SKU", deployment_service.attributes)

            try:
                group_name = self._get_group_name(request, sandbox_id)

                vm = self.vm_service.get_vm(compute_client, group_name, vm_name)
                result = self.vm_details_provider.create(vm, is_market_place, logger, network_client, sandbox_id)

            except Exception as e:
                logger.error("Error getting vm details for '{0}': {1}".format(vm_name, traceback.format_exc()))
                result = VmDetailsData(errorMessage=e.message)

            result.appName = vm_name
            results.append(result)

        return results

    def _get_group_name(self, request, sandbox_id):
        group_name = \
            self.vm_custom_params_extractor.get_resource_group_name(request.deployedAppJson.vmdetails.vmCustomParams)
        if not group_name:
            group_name = sandbox_id

        return group_name
