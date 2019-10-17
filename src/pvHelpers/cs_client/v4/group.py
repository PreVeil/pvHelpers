from pvHelpers.crypto import PVKeyFactory
from pvHelpers.user import LocalUser, UserDBNode
from pvHelpers.utils import b64enc, params

from ..utils import ServerResponseError


class GroupV4(object):
    @params(object, LocalUser, unicode)
    def getGroupInfo(self, user, group_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/groups", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
                        "user_id": user.user_id, "group_id": group_id})
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode)
    def createGroup(self, user, group_name):
        user_public_key = user.user_key.encryption_key.public_key

        admin_group_key, serialized_group_key, wrapped_group_private_key = createCollectionKey(0, user_public_key)

        admin_group_public_user_key = admin_group_key.public_user_key

        admin_group_public_key = admin_group_public_user_key.public_key

        group_owner_key, serialized_group_owner_key, wrapped_group_owner_private_key = createCollectionKey(0, admin_group_public_key)
        group_sharer_key, serialized_group_sharer_key, wrapped_group_sharer_private_key = createCollectionKey(0, admin_group_public_key)
        group_log_viewer_key, serialized_group_log_viewer_key, wrapped_group_log_viewer_private_key = createCollectionKey(0, admin_group_public_key)

        public_keys = {
            u"owner"      : serialized_group_owner_key,
            u"sharer"     : serialized_group_sharer_key,
            u"log_viewer" : serialized_group_log_viewer_key,
        }

        wrapped_keys = {
            u"owner"      : wrapped_group_owner_private_key,
            u"sharer"     : wrapped_group_sharer_private_key,
            u"log_viewer" : wrapped_group_log_viewer_private_key,
        }

        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/groups", "POST", {
                u"user_id"            : user.user_id,
                u"name"               : group_name,
                u"group_key"          : serialized_group_key,
                u"wrapped_group_key"  : wrapped_group_private_key,
                u"public_keys"        : public_keys,
                u"wrapped_keys"       : wrapped_keys,
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        data = resp.json()

        group_id = data.get("group_id")
        if group_id is None:
            raise ServerResponseError("createGroup: server response missing group_id")

        return group_id, admin_group_public_user_key, wrapped_group_private_key

# UGH, get rid of this!!!!
def createCollectionKey(version, public_key):
    new_key = PVKeyFactory.newUserKey(version)

    # don't B64 encode for filesync
    wrapped_private_key = b64enc(public_key.seal(new_key.buffer.SerializeToString()))

    return new_key, new_key.public_user_key.serialize(), wrapped_private_key