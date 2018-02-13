from community.constants import *


groups_templates = {"community_moderator": COMMUNITY_MODERATOR,
                    "community_leader": COMMUNITY_LEADER}

community_moderator_permissions = [
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

community_leader_permissions = community_moderator_permissions + [
    "change_community",
    "add_community"
]

group_permissions = {
    "community_moderator": community_moderator_permissions,
    "community_leader": community_leader_permissions
}
