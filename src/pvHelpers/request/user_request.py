import datetime
import types
import uuid

from pvHelpers.user import LocalUser
from pvHelpers.utils import b64enc, jdumps, jloads, params, utf8Encode

REQUEST_EXPIRATION_DAYS = 7


class UserRequest(object):
    __protocol_version__ = 1
    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        data = jloads(serialized_req)
        self.user_id = data["user_id"]
        self.type = data["type"]
        self.timestamp = data["timestamp"]
        self.expiration = data["expiration"]
        self.device_id = data["device_id"]
        self.data = data["data"]
        self.serialized_req = serialized_req
        self.signature = signature
        self.request_id = request_id


class MemberAPGChangeRequest(UserRequest):
    __type__ = u"set_member_approval_group"

    @classmethod
    @params(object, LocalUser, {
        "current_group_id": {types.NoneType, unicode},
        "current_group_version": {types.NoneType, unicode},
        "events": [{"user_id": unicode, "signature": unicode, "payload": unicode}],
        "requester_key_version": {int, long}})
    def new(cls, user, apg_set_events):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": apg_set_events,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(MemberAPGChangeRequest, self).__init__(serialized_req, signature, request_id)


class MemberRekeyAndAPGChangeRequest(UserRequest):
    __type__ = u"member_rekey_and_set_approval_group"

    @classmethod
    @params(object, LocalUser, {
        "current_group_id": {types.NoneType, unicode},
        "current_group_version": {types.NoneType, unicode},
        "events": [{"user_id": unicode, "signature": unicode, "payload": unicode}],
        "requester_key_version": {int, long}})
    def new(cls, user, apg_set_events):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": apg_set_events,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(MemberRekeyAndAPGChangeRequest, self).__init__(serialized_req, signature, request_id)


class APGChangeRequest(UserRequest):
    __type__ = u"change_approval_group"

    @classmethod
    @params(object, LocalUser, {
        "group": [{"user_id": unicode, "required": bool, "secret": unicode, "protocol_version": int}],
        "optionals_required": int})
    def new(cls, user, new_apg):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": new_apg,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(APGChangeRequest, self).__init__(serialized_req, signature, request_id)


class RekeyAndAPGChangeRequest(UserRequest):
    __type__ = u"rekey_and_change_approval_group"

    @classmethod
    @params(object, LocalUser, {
        "public_key": unicode, "wrapped_last_key": unicode,
        "group": [{"user_id": unicode, "required": bool, "secret": unicode}],
        "optionals_required": {types.NoneType, int}})
    def new(cls, user, new_key_apg):
        # HACK: cuz of the `params` not being capable to handle `{None, [...]}`
        if new_key_apg["optionals_required"] is None:
            new_key_apg["group"] = None
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": new_key_apg,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(RekeyAndAPGChangeRequest, self).__init__(serialized_req, signature, request_id)


class GroupRoleChangeRequest(UserRequest):
    __type__ = u"change_org_approval_group_role"

    @classmethod
    @params(object, LocalUser, {"group_id": unicode, "version": unicode, "group_role": unicode})
    def new(cls, user, group_info):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": group_info,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(GroupRoleChangeRequest, self).__init__(serialized_req, signature, request_id)


class ExportRequest(UserRequest):
    __type__ = u"export"

    @classmethod
    @params(object, LocalUser, {"until": unicode, "users": [{"user_id": unicode, "key_version": {int, long}}]})
    def new(cls, user, export_params):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": export_params,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(ExportRequest, self).__init__(serialized_req, signature, request_id)

    def to_dict(self):
        return {
            "request_payload": self.serialized_req,
            "signature": self.signature,
            "request_id": self.request_id
        }


class MemberRoleChangeRequest(UserRequest):
    __type__ = u"change_admin_status"

    @classmethod
    @params(object, LocalUser, {"user_id": unicode, "department": {unicode, types.NoneType}, "role": unicode})
    def new(cls, user, change):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": change,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(MemberRoleChangeRequest, self).__init__(serialized_req, signature, request_id)


class MemberDeletionRequest(UserRequest):
    __type__ = u"delete_user"

    @classmethod
    @params(object, LocalUser, {"user_id": unicode})
    def new(cls, user, user_info):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": user_info,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(MemberDeletionRequest, self).__init__(serialized_req, signature, request_id)


class SubsumeAccountRequest(UserRequest):
    __type__ = u"subsume_account"

    @classmethod
    @params(object, LocalUser,
            {"subsume_user_id": unicode, "department": {unicode, types.NoneType}, "entity_id": unicode})
    def new(cls, user, subsume_info):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=REQUEST_EXPIRATION_DAYS)
        payload = jdumps({
            "user_id": user.user_id,
            "device_id": user.device.id,
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "type": cls.__type__,
            "data": subsume_info,
            "protocol_version": cls.__protocol_version__
        })
        request_id = u"__local__" + unicode(uuid.uuid4())
        return cls(payload, b64enc(user.user_key.signing_key.sign(utf8Encode(payload))), request_id)

    @params(object, unicode, unicode, unicode)
    def __init__(self, serialized_req, signature, request_id):
        super(SubsumeAccountRequest, self).__init__(serialized_req, signature, request_id)
