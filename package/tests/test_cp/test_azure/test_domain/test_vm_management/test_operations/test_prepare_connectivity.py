import uuid
from threading import Lock
from unittest import TestCase

from mock import MagicMock, Mock
from msrestazure.azure_exceptions import CloudError

from cloudshell.cp.azure.common.exceptions.virtual_network_not_found_exception import VirtualNetworkNotFoundException
from cloudshell.cp.azure.domain.services.key_pair import KeyPairService
from cloudshell.cp.azure.domain.services.security_group import SecurityGroupService
from cloudshell.cp.azure.domain.services.tags import TagService
from cloudshell.cp.azure.domain.vm_management.operations.PrepareSandboxInfraOperation import \
    PrepareSandboxInfraOperation
from tests.helpers.test_helper import TestHelper
from cloudshell.cp.core.models import PrepareCloudInfra, PrepareSubnet, CreateKeys, PrepareCloudInfraParams, \
    PrepareSubnetParams


class TestPrepareSandboxInfra(TestCase):
    def setUp(self):
        self.storage_service = MagicMock()
        self.cancellation_service = MagicMock()
        self.task_waiter_service = MagicMock()
        self.vm_service = MagicMock()
        self.network_service = MagicMock()
        self.tag_service = TagService()
        self.key_pair_service = KeyPairService(storage_service=self.storage_service)
        self.security_group_service = SecurityGroupService(self.network_service)
        self.logger = MagicMock()
        self.name_provider_service = MagicMock()
        self.resource_id_parser = MagicMock()

        self.prepare_connectivity_operation = PrepareSandboxInfraOperation(
            vm_service=self.vm_service,
            network_service=self.network_service,
            storage_service=self.storage_service,
            tags_service=self.tag_service,
            key_pair_service=self.key_pair_service,
            security_group_service=self.security_group_service,
            name_provider_service=self.name_provider_service,
            subnet_locker=Lock(),
            cancellation_service=self.cancellation_service,
            resource_id_parser=self.resource_id_parser)

    def test_prepare_connectivity(self):
        # Arrange
        self.key_pair_service.generate_key_pair = MagicMock()
        self.key_pair_service.save_key_pair = MagicMock()
        self.network_service.get_virtual_network_by_tag = MagicMock()
        self.storage_service.create_storage_account = MagicMock()
        self.vm_service.create_resource_group = MagicMock()

        network_action = PrepareCloudInfra()
        network_action.actionParams = PrepareCloudInfraParams
        network_action.actionParams.cidr = "10.0.0.0/24"
        network_action.actionId = '1'
        subnet_action = PrepareSubnet()
        subnet_action.actionParams = PrepareSubnetParams
        subnet_action.actionParams.cidr = "10.0.0.0/24"
        subnet_action.actionParams.subnetServiceAttributes = dict()
        subnet_action.actionId = '1'
        create_keys_action = CreateKeys()
        create_keys_action.actionId = '3'

        actions = [network_action, subnet_action, create_keys_action]
        result = Mock()
        result.wait = Mock()

        network_client = MagicMock()
        network_client.subnets.create_or_update = Mock(return_value=result)
        network_client.virtual_networks.list = Mock(return_value="test")
        network_client.security_rules.list = Mock(return_value=[])
        network_client._rule_priority_generator = Mock(return_value=[1111, 2222, 3333, 4444])
        network_client.security_rules.create_or_update = Mock()
        network_client.network_security_groups.create_or_update = Mock()
        cancellation_context = MagicMock()
        self.prepare_connectivity_operation._cleanup_stale_data = MagicMock()

        # Act
        self.prepare_connectivity_operation.prepare_connectivity(
            reservation=MagicMock(),
            cloud_provider_model=MagicMock(),
            storage_client=MagicMock(),
            resource_client=MagicMock(),
            network_client=network_client,
            logger=MagicMock(),
            actions=actions,
            cancellation_context=cancellation_context)

        # Verify
        # Created resource Group
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.vm_service.create_resource_group))

        # created Storage account
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.storage_service.create_storage_account))
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.network_service.get_virtual_network_by_tag, 2))

        # key pair created
        self.assertTrue(TestHelper.CheckMethodCalledXTimes(self.key_pair_service.save_key_pair))

        self.assertTrue(TestHelper.CheckMethodCalledXTimes(network_client.security_rules.create_or_update, 3))
        network_client.network_security_groups.create_or_update.assert_called_once()
        self.cancellation_service.check_if_cancelled.assert_called_with(cancellation_context)

    def test_prepare_storage_account_name(self):
        # Arrange
        reservation_id = "some-id"
        self.name_provider_service.generate_name = Mock(return_value="{0}-{1}".format(reservation_id, "guid"))

        # Act
        res = self.prepare_connectivity_operation._prepare_storage_account_name(reservation_id)

        # Assert
        self.name_provider_service.generate_name.assert_called_once_with(name="someid", postfix="cs",
                                                                         max_length=24)
        self.assertEquals(res, "someidguid")

    def test_extract_cidr_throws_error(self):
        action = Mock()
        action.connectionParams.cidr = None

        actions = [action]

        self.assertRaises(ValueError,
                          self.prepare_connectivity_operation._validate_request_and_extract_cidr,
                          actions)

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

        network_action = PrepareCloudInfra()
        network_action.actionParams = PrepareCloudInfraParams()
        network_action.actionParams.cidr = "10.0.0.0/24"
        network_action.actionId = '1'
        subnet_action = PrepareSubnet()
        subnet_action.actionParams = PrepareSubnetParams()
        subnet_action.actionParams.cidr = "10.0.0.0/24"
        subnet_action.actionId = '1'
        create_keys_action = CreateKeys()
        create_keys_action.actionId = '3'

        actions = [network_action, subnet_action, create_keys_action]

        reservation = MagicMock()
        reservation.reservation_id = str(uuid.uuid4())
        cancellation_context = MagicMock()
        # Act

        self.assertRaises(VirtualNetworkNotFoundException,
                          self.prepare_connectivity_operation.prepare_connectivity,
                          reservation=reservation,
                          cloud_provider_model=MagicMock(),
                          storage_client=MagicMock(),
                          resource_client=MagicMock(),
                          network_client=MagicMock(),
                          logger=self.logger,
                          actions=actions,
                          cancellation_context=cancellation_context)

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
                          actions=actions,
                          cancellation_context=cancellation_context)

    def test_cleanup_stale_data(self):
        """Check that method will clean up subnet and related resource groups"""
        network_client = MagicMock()
        resource_client = MagicMock()
        cloud_provider_model = MagicMock()
        subnet_cidr = "10.10.10.10/24"
        subnet = MagicMock(address_prefix=subnet_cidr, ip_configurations=[MagicMock(), MagicMock()])
        sandbox_vnet = MagicMock(subnets=[subnet])
        self.resource_id_parser.get_resource_group_name.side_effect = ["resource_group1", "resource_group2"]

        # Act
        self.prepare_connectivity_operation._cleanup_stale_data(network_client=network_client,
                                                                resource_client=resource_client,
                                                                cloud_provider_model=cloud_provider_model,
                                                                sandbox_vnet=sandbox_vnet,
                                                                subnet_cidr=subnet_cidr,
                                                                logger=self.logger)

        # Verify
        self.network_service.delete_subnet.assert_called_once_with(
            group_name=cloud_provider_model.management_group_name,
            network_client=network_client,
            subnet_name=subnet.name,
            vnet_name=sandbox_vnet.name)

        self.network_service.update_subnet.assert_called_once_with(
            network_client=network_client,
            resource_group_name=cloud_provider_model.management_group_name,
            virtual_network_name=sandbox_vnet.name,
            subnet_name=subnet.name,
            subnet=subnet)

    def test_create_subnet_calls_cleanup_stale_data(self):
        """Check that method will call _cleanup_stale_data method on CloudError"""
        network_client = MagicMock()
        resource_client = MagicMock()
        cloud_provider_model = MagicMock()
        network_security_group = MagicMock()
        subnet_cidr = "10.10.10.10/24"
        subnet_name = "test_subnet_name"
        subnet = MagicMock(address_prefix=subnet_cidr, ip_configurations=[MagicMock(), MagicMock()])
        sandbox_vnet = MagicMock(subnets=[subnet])
        self.prepare_connectivity_operation._cleanup_stale_data = MagicMock()
        self.network_service.create_subnet.side_effect = [CloudError(MagicMock(__str__=MagicMock(
            return_value="NetcfgInvalidSubnet")),
            error=True), MagicMock()]

        # Act
        self.prepare_connectivity_operation._create_subnet(
            cidr=subnet_cidr,
            cloud_provider_model=cloud_provider_model,
            logger=self.logger,
            network_client=network_client,
            resource_client=resource_client,
            network_security_group=network_security_group,
            sandbox_vnet=sandbox_vnet,
            subnet_name=subnet_name)

        # Verfy
        self.prepare_connectivity_operation._cleanup_stale_data.assert_called_once_with(
            cloud_provider_model=cloud_provider_model,
            network_client=network_client,
            resource_client=resource_client,
            sandbox_vnet=sandbox_vnet,
            subnet_cidr=subnet_cidr,
            logger=self.logger)
