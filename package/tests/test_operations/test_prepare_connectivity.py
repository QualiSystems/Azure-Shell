from unittest import TestCase

import jsonpickle

from cloudshell.cp.azure.common.deploy_data_holder import DeployDataHolder

from tests.helpers.test_helper import TestHelper

from cloudshell.cp.azure.domain.services.key_pair import KeyPairService

from cloudshell.cp.azure.domain.services.tags import TagService

from cloudshell.cp.azure.domain.services.network_service import NetworkService

from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService

from cloudshell.cp.azure.domain.services.storage_service import StorageService

from cloudshell.cp.azure.domain.vm_management.operations.prepare_connectivity_operation import \
    PrepareConnectivityOperation
from mock import MagicMock


class TestPrepareConnectivity(TestCase):
    def setUp(self):
        self.storage_service = StorageService()
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.tag_service = TagService()
        self.key_pair_service = KeyPairService()
        self.logger = MagicMock()

        self.prepare_connectivity_operation = PrepareConnectivityOperation(logger=self.logger,
                                                                           vm_service=self.vm_service,
                                                                           network_service=self.network_service,
                                                                           storage_service=self.storage_service,
                                                                           tags_service=self.tag_service,
                                                                           key_pair_service=self.key_pair_service)

    def test_prepare_connectivity(self):
        # Arrange
        self.key_pair_service.save_key_pair = MagicMock()
        self.key_pair_service.generate_key_pair = MagicMock()
        self.network_service.get_virtual_network_by_tag = MagicMock()
        self.storage_service.create_storage_account = MagicMock()
        self.vm_service.create_resource_group = MagicMock()
        self.network_service.get_virtual_networks = MagicMock()
        self.network_service.create_subnet = MagicMock()

        req = MagicMock()
        action = MagicMock()
        att = MagicMock()
        att.attributeName = 'Network'
        att.attributeValue = '10.0.0.0/12'
        action.customActionAttributes = [att]
        req.actions = [action]
        prepare_connectivity_request = req
        # Act

        self.prepare_connectivity_operation.prepare_connectivity(
            reservation=MagicMock(),
            cloud_provider_model=MagicMock(),
            storage_client=MagicMock(),
            resource_client=MagicMock(),
            network_client=MagicMock(),
            logger=self.logger,
            request=prepare_connectivity_request)

        # Verify
        # Created resource Group
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.create_resource_group))

        # created Storage account
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.storage_service.create_storage_account))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.network_service.get_virtual_network_by_tag, 2))

        # key pair created
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.key_pair_service.save_key_pair))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.network_service.get_virtual_networks))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.network_service.create_subnet))
