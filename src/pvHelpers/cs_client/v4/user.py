import types

from pvHelpers.crypto import PVKeyFactory
from pvHelpers.crypto.user_key import PublicUserKeyBase
from pvHelpers.crypto.utils import hex_encode, sha_256_sum
from pvHelpers.logger import g_log
from pvHelpers.user import LocalUser, OrganizationInfo, User, UserGroup
from pvHelpers.utils import (b64dec, b64enc, CaseInsensitiveDict, jloads,
                             params, utf8_encode)
import requests

from ..utils import ServerResponseError

EXISTS = "exists"


class UserV4(object):
    @params(object, LocalUser, int)
    def get_user_groups(self, user, seq):
        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/users/groups/user", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            u"user_id": user.user_id,
            u"seq": seq
        })
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode)
    def get_user_shards(self, user, for_user_id):
        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/users/approvers/shard", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            u"user_id": user.user_id,
            u"for_user_id": for_user_id
        })
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, {unicode, types.NoneType})
    def get_user_approval_group(self, user, user_id=None):
        if not user_id:
            user_id = user.user_id
        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/users/approvers/info", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={"user_id": user_id})
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, {int, long})
    def fetch_user(self, user, user_id, key_version=-1):
        user_data = self.fetchUsers(user, [(user_id, key_version)])
        if len(user_data) != 1 or user_id not in user_data:
            return None
        return user_data[user_id]

    @params(object, LocalUser, [(unicode, int)])
    def fetch_users(self, user, user_ids):
        user_ids = list(set(user_ids))
        query_data = []
        for x in user_ids:
            if len(x) != 2:
                raise TypeError(u"expected (user_id, version) tuple")
            query_data.append({"user_id": x[0], "key_version": x[1]})

        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/users/find", "POST", {
                "spec":  query_data
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        data = resp.json()
        users = data["users"]
        output = CaseInsensitiveDict()
        org_ids = set(map(lambda u: u["entity_id"], users))
        org_infos = {id_: self.get_org_info(user, id_) for id_ in org_ids if id_}
        # TODO: take account_version into account!
        # make deserialization more explicit, add checks for key_versions
        for u in users:
            organiztion_info = OrganizationInfo(
                u["entity_id"], org_infos[u["entity_id"]]["display_name"],
                u["entity_metadata"]["department"], u["entity_metadata"]["role"]
            ) if u["entity_id"] else None

            public_user_keys = []
            if u["public_key"]:
                public_user_keys = [PVKeyFactory.deserialize_public_user_key(u["public_key"])]

            user = User(
                u["user_id"], u["account_version"], u["display_name"], u["mail_collection_id"],
                public_user_keys, organiztion_info
            )
            if user.user_id in output:
                output[user.user_id].public_user_keys += [user.public_user_key]
            else:
                output[user.user_id] = user

        for ug in data["groups"]:
            output[ug["alias"]] = UserGroup(ug["alias"], ug["users"])

        return output

    @params(object, LocalUser, unicode)
    def invite_user(self, user, invitee_id):
        g_log.info("inviteUser: {}, {}".format(user.user_id, invitee_id))
        url, raw_body, headers = self.prepare_signed_request(
            user, u"/users/invite", "PUT", {
                "user_id": user.user_id,
                "invitee_email": invitee_id
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()

        invitee_user = None
        try:
            data = resp.json()
            if data["status"] == EXISTS:
                u = data["user"]
                organiztion_info = OrganizationInfo(
                    u["entity_id"], u"",
                    u["entity_metadata"]["department"], u["entity_metadata"]["role"]
                ) if u["entity_id"] else None

                public_user_keys = []
                if u["public_key"]:
                    public_user_keys = [PVKeyFactory.deserialize_public_user_key(u["public_key"])]

                invitee_user = User(
                    u["user_id"], u["account_version"], u["display_name"], u["mail_collection_id"],
                    public_user_keys, organiztion_info
                )
        except (KeyError, ValueError) as e:
            raise ServerResponseError(e)

        return invitee_user

    @params(object, LocalUser)
    def fetch_log_keys(self, user):
        url, raw_body, headers = self.prepare_signed_request(
            user, "/users/log_keys", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={u"user_id": user.user_id})
        resp.raise_for_status()

        text = resp.text
        if resp.encoding != "utf-8" or not isinstance(text, unicode):
            raise ServerResponseError("fetchLogKeys: bad encoding to response")
        data = jloads(text)

        log_keys = data.get("log_keys")
        if log_keys is None:
            raise ServerResponseError("fetchLogKeys: server response missing log keys")

        return log_keys

    @params(object, LocalUser, unicode, PublicUserKeyBase, unicode, str, int)
    def grant_group_key_to_user(self, user, recipient_id, recipient_public_key, group_id, group_key, group_key_version):
        g_log.info("{} granting to {} ".format(user.user_id, recipient_id))
        wrapped_group_key = b64enc(recipient_public_key.public_key.seal(group_key))

        to_hash_group_key = b64dec(wrapped_group_key)
        hashed_wrapped_key = sha_256_sum(to_hash_group_key)

        text_to_sign = recipient_id.lower() + "," + str(recipient_public_key.key_version) + \
            "," + group_id + "," + str(group_key_version) + "," + hex_encode(hashed_wrapped_key).lower()

        signature = b64enc(user.user_key.signing_key.sign(utf8_encode(text_to_sign)))

        url, raw_body, headers = self.prepare_signed_request(
            user, u"/users/groups/user", "PUT", {
                "user_id": user.user_id,
                "sharee_user_id": recipient_id,
                "group_id": group_id,
                "user_key_version": recipient_public_key.key_version,
                "group_key_version": group_key_version,
                "signature": signature,
                "wrapped_key": wrapped_group_key
            }
        )
        resp = self.put(url, headers, raw_body)
        if resp.status_code == requests.codes.conflict:
            g_log.error("grantGroupKeyToUser: user already has group key")
            return
        resp.raise_for_status()
        return

    @params(object, LocalUser, unicode, unicode, int, unicode, unicode, int)
    def grant_wrapped_key_to_group(self, user, collection_id, wrapped_key,
                                   key_version, role, group_id, group_key_version):
        g_log.info("{} granting to {}".format(user.user_id, group_id))
        to_hash_key_for_group = b64dec(wrapped_key)
        hashed_wrapped_key = sha_256_sum(to_hash_key_for_group)

        text_to_sign = group_id + "," + str(group_key_version) + "," + collection_id + "," + \
            role.upper() + "," + str(key_version) + "," + hex_encode(hashed_wrapped_key).lower()

        signature = b64enc(user.user_key.signing_key.sign(utf8_encode(text_to_sign)))

        url, raw_body, headers = self.prepare_signed_request(
            user, u"/users/collection/grant", "PUT", {
                "user_id": user.user_id,
                "collection_id": collection_id,
                "roles": [{
                    "role": role.lower(),
                    "version": key_version
                }],
                "groups": [{
                    "group_id": group_id,
                    "key_version": group_key_version,
                    "role_info": [{
                        "role": role.lower(),
                        "signature": signature,
                        "wrapped_key": wrapped_key,
                    }]
                }]
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return

    def set_user_approval_group(self, user, approvers_group, optional_count):
        url, raw_body, headers = self.prepare_signed_request(
            user, u"/users/approvers", "POST", {
                "user_id": user.user_id,
                "group": approvers_group,
                "optionals_required": optional_count
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
