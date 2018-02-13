from django.test import TestCase

from community.constants import (COMMUNITY_MODERATOR, COMMUNITY_LEADER)
from community.permissions import (community_moderator_permissions,
                                   community_leader_permissions,
                                   group_permissions, groups_templates)


class PermissionsTestCase(TestCase):
    def test_community_moderator_permissions(self):
        """Test community moderator list of permissions"""
        permissions = [
            "add_tag",
            "change_tag",
            "add_resourcetype",
            "change_resourcetype",
            "add_community_news",
            "change_community_news",
            "add_community_resource",
            "change_community_resource",
            "delete_tag",
            "delete_resourcetype",
            "delete_community_news",
            "delete_community_resource",
            "add_community_page",
            "change_community_page",
            "delete_community_page",
            "approve_community_comment",
            "delete_community_comment",
            "add_community_systersuser",
            "change_community_systersuser",
            "delete_community_systersuser",
            "approve_community_joinrequest"
        ]
        self.assertCountEqual(community_moderator_permissions, permissions)

    def test_community_leader_permissions(self):
        """Test community leader list of permissions"""
        permissions = [
            "add_tag",
            "change_tag",
            "add_resourcetype",
            "change_resourcetype",
            "add_community_news",
            "change_community_news",
            "add_community_resource",
            "change_community_resource",
            "delete_tag",
            "delete_resourcetype",
            "delete_community_news",
            "delete_community_resource",
            "add_community_page",
            "change_community_page",
            "delete_community_page",
            "approve_community_comment",
            "delete_community_comment",
            "add_community_systersuser",
            "change_community_systersuser",
            "delete_community_systersuser",
            "approve_community_joinrequest",
            "change_community",
            "add_community",
        ]
        self.assertCountEqual(community_leader_permissions, permissions)

    def test_group_permissions(self):
        """Test group permissions keys"""
        self.assertTrue("community_moderator" in group_permissions)
        self.assertTrue("community_leader" in group_permissions)

    def test_group_templates(self):
        """Test group templates values"""
        self.assertEqual(groups_templates["community_moderator"],
                         COMMUNITY_MODERATOR)
        self.assertEqual(groups_templates["community_leader"], COMMUNITY_LEADER)
