import types
from SSSA import sssa
from .shard import new as newShard
from .export_shard import new as newExportShard
from pvHelpers.utils import params, utf8Encode, utf8Decode
from pvHelpers.crypto.user_key import UserKeyBase, PublicUserKeyBase
from pvHelpers.user.user import User

# Information provided by the backend about an approver
class ApproverData(object):
    @params(object, unicode, unicode)
    def __init__(self, user_id, display_name):
        self.user_id = user_id
        self.display_name = display_name

    def toDict(self):
        return {"user_id" : self.user_id, "display_name" : self.display_name}

class ApprovalGroup(object):
    @staticmethod
    @params(unicode, [{"user_id": unicode, "display_name": unicode}], [{"user_id": unicode, "display_name": unicode}], int)
    def new(user_id, required_users, optional_users, optionals_required):
        xs = required_users
        required_users = []
        for x in xs:
            approver = ApproverData(x.get("user_id"), x.get("display_name"))
            required_users.append(approver)

        xs = optional_users
        optional_users = []
        for x in xs:
            approver = ApproverData(x.get("user_id"), x.get("display_name"))
            optional_users.append(approver)

        return ApprovalGroup(user_id, required_users, optional_users, optionals_required)

    def __init__(self, user_id, required_users, optional_users, optionals_required):
        self.user_id = user_id
        self.required_users = required_users
        self.optional_users = optional_users
        self.optionals_required = int(optionals_required)

        assert self.optionals_required <= len(self.optional_users)

    def toDict(self):
        return {
            "user_id" : self.user_id,
            "required_users" : [x.toDict() for x in self.required_users],
            "optional_users" : [x.toDict() for x in self.optional_users],
            "optionals_required" : self.optionals_required
        }


    @params(object, UserKeyBase, unicode, {User}, bool, {int, long, types.NoneType})
    def generateShardedSecret(self, approvee_user_key, secret, approvers, for_export=False, wrapped_key_version=None):
        required_parts_count = len(self.required_users)
        if self.optionals_required > 0:
            required_parts_count += 1

        bits = utf8Encode(secret)
        required_parts = sssa().create(required_parts_count, required_parts_count, bits)

        # Generate the optionals
        if self.optionals_required > 0:
            optionals_secret = required_parts.pop()
            optional_parts = sssa().create(self.optionals_required, len(self.optional_users), optionals_secret)

        group = []
        for approver_data in self.required_users:
            if approver_data.user_id not in approvers:
                raise KeyError(u"missing {} User instance in approvers list".format(approver_data.user_id))
            approver = approvers[approver_data.user_id]

            if for_export:
                encrypted_shard = newExportShard(
                    approvee_user_key, approver.user_id, approver.public_user_key, wrapped_key_version,
                    required_parts.pop(), True)
            else:
                encrypted_shard = newShard(
                    approvee_user_key, approver.user_id, approver.public_user_key,
                    required_parts.pop(), True)
            group.append(encrypted_shard.toDict())

        for approver_data in self.optional_users:
            if approver_data.user_id not in approvers:
                raise KeyError(u"missing {} User instance in approvers list".format(approver_data.user_id))
            approver = approvers[approver_data.user_id]
            if for_export:
                encrypted_shard = newExportShard(
                    approvee_user_key, approver.user_id, approver.public_user_key, wrapped_key_version,
                    optional_parts.pop(), False)
            else:
                encrypted_shard = newShard(
                    approvee_user_key, approver.user_id, approver.public_user_key,
                    optional_parts.pop(), False)

            group.append(encrypted_shard.toDict())

        return group

    def reconstructSecret(self, required_shards, optional_shards):
        if self.optionals_required > 0:
            # combine() can't handle empty list
            if len(optional_shards) < 1:
                raise ValueError(u"reconstructSecret: can't pass empty `optional_shards` to combine()")
            optional_shard = sssa().combine(optional_shards)
            required_shards.append(optional_shard)

        # combine() can't handle empty list
        if len(required_shards) < 1:
            raise ValueError("reconstructSecret: can't pass empty `required_shards` to combine()")
        raw_secret = sssa().combine(required_shards)
        secret = utf8Decode(raw_secret)
        return secret
