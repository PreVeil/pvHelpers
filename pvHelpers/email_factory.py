import types
from .email import EmailException, PROTOCOL_VERSION, Content, AttachmentMetadata, \
                   EmailV1, EmailV2, EmailV3, EmailV4, ServerAttributes, Attachment
from .misc import MergeDicts, NOT_ASSIGNED, jloads, toInt, g_log
from .params import params
from .crypto import SymmKeyBase

#########################################
######### Email Entity Factory ##########
#########################################
class EmailFactory(object):
    @staticmethod
    def new(*args, **kwargs):
        v = kwargs.get("protocol_version", None)
        if v is None:
            raise EmailException(u"EmailFactory.new: Missing protocol_version named argument")

        kwargs.pop("protocol_version", None)

        if v is PROTOCOL_VERSION.V1:
            return EmailV1(*args, **kwargs)
        elif v is PROTOCOL_VERSION.V2:
            return EmailV2(*args, **kwargs)
        elif v is PROTOCOL_VERSION.V3:
            return EmailV3(*args, **kwargs)
        elif v is PROTOCOL_VERSION.V4:
            return EmailV4(*args, **kwargs)

        raise EmailException(u"EmailFactory.new: Unsupported protocol_version")

    @staticmethod
    def fromDB(revision_id, version, server_id, metadata, server_time, flags, uid, mailbox_server_id, thread_id, mailbox_name, expunged):
        if server_id is None: # An email not having server_id means it's a local email
            server_info = NOT_ASSIGNED()
        else:
            server_info = ServerAttributes(server_id, revision_id, mailbox_server_id, mailbox_name, version, uid, thread_id, server_time, expunged)

        status, flags = jloads(flags)
        if status == False:
            raise EmailException(u"EmailFactory.fromDB: bad flags json")

        status, metadata = jloads(metadata)
        if status == False:
            raise EmailException(u"EmailFactory.fromDB: bad metadata json")

        status, v = toInt(metadata.get("protocol_version"))
        if status == False:
            raise EmailException(u"EmailFactory.fromDB: protocol_version must coerce to int")

        metadata.pop("protocol_version", None)

        metadata.update({
            "body": Content(block_ids=metadata["body"]["block_ids"], wrapped_key=metadata["body"]["wrapped_key"], key_version=metadata["body"]["key_version"]),
            "attachments": [Attachment.fromDict(att_dict) for att_dict in metadata.get("attachments")]
        })

        if v is PROTOCOL_VERSION.V1:
            return EmailV1(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V2:
            return EmailV2(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V3:
            return EmailV3(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V4:
            return EmailV4(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))


        raise EmailException(u"EmailFactory.fromDict: Unsupported protocol_version")

    @staticmethod
    # TODO: give required props. in params
    @params(dict, unicode, int, {object, types.NoneType})
    def fromServerMessage(msg, wrapped_key, key_version, mailbox):
        email_dict = {
            "server_attr": ServerAttributes(
                msg["id"], msg["rev_id"], msg["mailbox_id"], mailbox.name if mailbox else u"Unfetched", msg["version"], msg["uid"],
                msg["thread_id"], msg["timestamp"], msg["is_deleted"]
            ),
            "flags": msg["flags"],
            "body": Content(None, map(lambda b: b["id"], msg["body"]["blocks"]), wrapped_key, key_version),
            "sender": {"user_id": msg["private_metadata"]["sender"], "display_name": msg["private_metadata"]["sender"]},
            "tos": map(lambda u: {"user_id": u["user_id"], "display_name": u}, msg["private_metadata"]["tos"]) if msg["protocol_version"] is PROTOCOL_VERSION.V4 else msg["private_metadata"]["tos"],
            "ccs": map(lambda u: {"user_id": u, "display_name": u}, msg["private_metadata"].get("ccs", [])) if msg["protocol_version"] is PROTOCOL_VERSION.V4 else msg["private_metadata"].get("ccs", []),
            "bccs": map(lambda u: {"user_id": u, "display_name": u}, msg["private_metadata"].get("bccs", [])) if msg["protocol_version"] is PROTOCOL_VERSION.V4 else msg["private_metadata"].get("bccs", []),
            "subject": msg["private_metadata"]["subject"],
            "attachments": [Attachment(
                AttachmentMetadata(att["name"], att["metadata"].get("content_type"), att["metadata"].get("content_disposition"), att["metadata"].get("content_id"), att["size"]),
                Content(None, map(lambda b: b["id"], att["blocks"]), wrapped_key, key_version)
            ) for att in msg["attachments"]],
            "message_id": msg["message_id"],
            "snippet": msg["body"].get("snippet"),
            "in_reply_to": msg["in_reply_to"],
            "references": msg["references"],
            "reply_tos": [],
            "protocol_version": msg["protocol_version"],
            "other_headers": msg["private_metadata"].get("other_headers")
        }
        if msg["protocol_version"] is PROTOCOL_VERSION.V1:
            return EmailV1(**email_dict)
        elif msg["protocol_version"] is PROTOCOL_VERSION.V2:
            return EmailV2(**email_dict)
        elif msg["protocol_version"] is PROTOCOL_VERSION.V3:
            return EmailV3(**email_dict)
        elif msg["protocol_version"] is PROTOCOL_VERSION.V4:
            return EmailV4(**email_dict)

        raise EmailException("Unsupported protocol version {}".format(msg["protocol_version"]))
