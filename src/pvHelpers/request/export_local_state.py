from pvHelpers.utils import CaseInsensitiveDict, MergeDicts, params

from .user_request import ExportRequest


class ExportRequestLocalState(object):
    INIT = u"init"
    STARTED = u"started"
    CANCELLED = u"cancelled"
    DELETED = u"deleted"
    COMPLETED = u"completed"

    @classmethod
    @params(object, ExportRequest, dict, dict)
    def new(cls, request, approvers, group_info):
        return cls(request, approvers, ExportRequestLocalState.INIT, None, group_info)

    # approvers_info -> Map approver_id => {"approver_shards": ..., "approver_signature": unicode}
    # approver_shards ->
    # Map member_id => [{
    #   "sharder_key_version": {int, long},
    #   "key_version": {int, long}, "shard": unicode,
    #   "wrapped_key_version": unicode, "user_id": unicode
    # }]
    # @params(object, ExportRequest, approvers_info, unicode)
    def __init__(self, request, approvers_info, status, dropdir, group_info):
        self.request = request
        self.approvers_info = CaseInsensitiveDict({
            id_: MergeDicts(info, {"approver_shards": CaseInsensitiveDict(info["approver_shards"])})
            for id_, info in approvers_info.iteritems()
        })
        self.status = status
        self.dropdir = dropdir
        self.group_info = group_info

    def add_or_update_approver_info(self, approver_id, approver_info):
        self.approvers_info[approver_id] = MergeDicts(approver_info, {
            "approver_shards": CaseInsensitiveDict(approver_info["approver_shards"])
        })

    # NOTE: do not include decrypted shards!
    def to_dict(self):
        return {
            "request": self.request.to_dict(),
            "approvers_info": CaseInsensitiveDict({
                id_: MergeDicts(info, {
                    "approver_shards": CaseInsensitiveDict({
                        mid: map(lambda k: MergeDicts(k, {"shard": None}), m_keys)
                        for mid, m_keys in info["approver_shards"].iteritems()
                    }),
                }) for id_, info in self.approvers_info.iteritems()
            }),
            "status": self.status,
            "dropdir": self.dropdir,
            "group_info": self.group_info
        }

    def to_db(self):
        return {
            "request": self.request.to_dict(),
            "approvers_info": self.approvers_info,
            "status": self.status,
            "dropdir": self.dropdir,
            "group_info": self.group_info
        }

    @classmethod
    def from_db(cls, key_dict):
        req = key_dict["request"]
        return cls(
            ExportRequest(req["request_payload"], req["signature"], req["request_id"]),
            key_dict["approvers_info"],
            key_dict["status"],
            key_dict["dropdir"],
            key_dict["group_info"]
        )
