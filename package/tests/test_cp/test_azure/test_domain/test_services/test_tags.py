from unittest import TestCase

from cloudshell.cp.azure.domain.services.tags import TagService


class TestTagService(TestCase):
    def setUp(self):
        self.tags_service = TagService()

    def test_try_find_tag_list_is_none(self):
        tags_list = None
        tag_key = "SomeKey"
        tag_value = self.tags_service.try_find_tag(tags_list=tags_list, tag_key=tag_key)
        self.assertIsNone(tag_value)

    def test_try_find_tag_keys_returns_none(self):
        tags_list = None
        tag_key = "SomeKey"
        tag_value = self.tags_service.try_find_tag(tags_list=tags_list, tag_key=tag_key)
        self.assertIsNone(tag_value)

    def test_try_find_tag_keys_returns_empty_dict(self):
        tags_list = {}
        tag_key = "SomeKey"
        tag_value = self.tags_service.try_find_tag(tags_list=tags_list, tag_key=tag_key)
        self.assertIsNone(tag_value)

    def test_try_find_tag_key_not_found(self):
        tags_list = {"NotMyKey": "Val1"}
        tag_key = "MyKey"
        tag_value = self.tags_service.try_find_tag(tags_list=tags_list, tag_key=tag_key)
        self.assertIsNone(tag_value)

    def test_try_find_tag_returns_key_value(self):
        tags_list = {"MyKey": "Val1"}
        # tags_list.keys = Mock(return_value={"MyKey" : "Val1"})
        tag_key = "MyKey"
        tag_value = self.tags_service.try_find_tag(tags_list=tags_list, tag_key=tag_key)
        self.assertEquals(tag_value, "Val1")
