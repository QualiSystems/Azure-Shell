import uuid
from unittest import TestCase
import mock

import jsonpickle

from cloudshell.cp.azure.common.deploy_data_holder import DeployDataHolder
from cloudshell.cp.azure.common.exceptions.virtual_network_not_found_exception import VirtualNetworkNotFoundException
from cloudshell.cp.azure.domain.services.security_group import SecurityGroupService

from tests.helpers.test_helper import TestHelper

from cloudshell.cp.azure.domain.services.key_pair import KeyPairService

from cloudshell.cp.azure.domain.services.tags import TagService

from cloudshell.cp.azure.domain.services.network_service import NetworkService

from cloudshell.cp.azure.domain.services.virtual_machine_service import VirtualMachineService

from cloudshell.cp.azure.domain.services.storage_service import StorageService

from cloudshell.cp.azure.domain.vm_management.operations.prepare_connectivity_operation import \
    PrepareConnectivityOperation
from mock import MagicMock, Mock


class TestPrepareConnectivity(TestCase):
    def setUp(self):
        self.storage_service = StorageService()
        self.vm_service = VirtualMachineService()
        self.network_service = NetworkService()
        self.tag_service = TagService()
        self.key_pair_service = KeyPairService(storage_service=self.storage_service)
        self.security_group_service = SecurityGroupService(self.network_service)
        self.logger = MagicMock()

        self.prepare_connectivity_operation = PrepareConnectivityOperation(
            vm_service=self.vm_service,
            network_service=self.network_service,
            storage_service=self.storage_service,
            tags_service=self.tag_service,
            key_pair_service=self.key_pair_service,
            security_group_service=self.security_group_service)

    @mock.patch("cloudshell.cp.azure.domain.vm_management.operations.prepare_connectivity_operation.OperationsHelper")
    def test_prepare_connectivity(self, operation_helper_class):
        # Arrange
        self.key_pair_service.save_key_pair = MagicMock()
        self.key_pair_service.generate_key_pair = MagicMock()
        self.network_service.get_virtual_network_by_tag = MagicMock()
        self.storage_service.create_storage_account = MagicMock()
        self.vm_service.create_resource_group = MagicMock()

        req = MagicMock()
        action = MagicMock()
        att = MagicMock()
        att.attributeName = 'Network'
        att.attributeValue = [1]
        action.customActionAttributes = [att]
        req.actions = [action]
        prepare_connectivity_request = req
        # Act
        result = Mock()
        result.wait = Mock()

        network_client = MagicMock()
        network_client.subnets.create_or_update = Mock(return_value=result)
        network_client.virtual_networks.list = Mock(return_value="test")
        network_client.security_rules.list = Mock(return_value=[])
        network_client._rule_priority_generator = Mock(return_value=[1111, 2222, 3333, 4444])
        network_client.security_rules.create_or_update = Mock()
        network_client.network_security_groups.create_or_update = Mock()

        self.prepare_connectivity_operation.prepare_connectivity(
            reservation=MagicMock(),
            cloud_provider_model=MagicMock(),
            storage_client=MagicMock(),
            resource_client=MagicMock(),
            network_client=network_client,
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
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(network_client.virtual_networks.list))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(network_client.subnets.create_or_update))

        self.assertTrue(TestHelper.CheckMethodCalledXTimes(network_client.security_rules.create_or_update, 2))
        network_client.network_security_groups.create_or_update.assert_called_once()

    def test_extract_cidr_throws_error(self):
        action = MagicMock()

        self.assertRaises(ValueError,
                          self.prepare_connectivity_operation._extract_cidr,
                          action)

        action = Mock()
        att = Mock()
        att.attributeName = 'Network'
        att.attributeValue = ''
        action.customActionAttributes = [att]

        self.assertRaises(ValueError,
                          self.prepare_connectivity_operation._extract_cidr,
                          action)

    def test_prepare_connectivity_throes_exception_on_unavailable_VNETs(self):
        # Arrange
        self.key_pair_service.save_key_pair = MagicMock()
        self.key_pair_service.generate_key_pair = MagicMock()
        self.storage_service.create_storage_account = MagicMock()
        self.vm_service.create_resource_group = MagicMock()
        self.network_service.get_virtual_networks = MagicMock()
        self.network_service.create_subnet = MagicMock()
        self.network_service.get_virtual_network_by_tag = Mock(return_value=None)
        self.network_service.get_virtual_network_by_tag.side_effect = [None, Mock()]

        req = MagicMock()
        action = MagicMock()
        att = MagicMock()
        att.attributeName = 'Network'
        att.attributeValue = '10.0.0.0/12'
        action.customActionAttributes = [att]
        req.actions = [action]
        prepare_connectivity_request = req
        reservation = MagicMock()
        reservation.reservation_id = str(uuid.uuid4())
        # Act

        self.assertRaises(VirtualNetworkNotFoundException,
                          self.prepare_connectivity_operation.prepare_connectivity,
                          reservation=reservation,
                          cloud_provider_model=MagicMock(),
                          storage_client=MagicMock(),
                          resource_client=MagicMock(),
                          network_client=MagicMock(),
                          logger=self.logger,
                          request=prepare_connectivity_request)

        self.network_service.get_virtual_network_by_tag = Mock(return_value=None)
        self.network_service.get_virtual_network_by_tag.side_effect = [Mock(), None]

        self.assertRaises(VirtualNetworkNotFoundException,
                          self.prepare_connectivity_operation.prepare_connectivity,
                          reservation=reservation,
                          cloud_provider_model=MagicMock(),
                          storage_client=MagicMock(),
                          resource_client=MagicMock(),
                          network_client=MagicMock(),
                          logger=self.logger,
                          request=prepare_connectivity_request)
