import types

from pvHelpers.utils import (EncodingException, jloads, MergeDicts, NOT_ASSIGNED,
                             params, toInt, WrapExceptions)

from .email import EmailV1, EmailV2, EmailV3, EmailV4, EmailV5, EmailV6
from .email.attachment import Attachment, AttachmentMetadata
from .email.content import Content
from .email.helpers import EmailException, EmailHelpers, PROTOCOL_VERSION
from .email.server_attributes import ServerAttributes


class EmailFactory(object):
    """ Email entity facotry """
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
        elif v is PROTOCOL_VERSION.V5:
            return EmailV5(*args, **kwargs)
        elif v is PROTOCOL_VERSION.V6:
            return EmailV6(*args, **kwargs)

        raise EmailException(u"EmailFactory.new: Unsupported protocol_version")

    @staticmethod
    @WrapExceptions(EmailException, [EncodingException])
    def from_db(revision_id, collection_id, version, server_id, metadata, server_time,
                flags, uid, mailbox_server_id, thread_id, mailbox_name, expunged):
        if server_id is None:  # An email not having server_id means it's a local email
            server_info = NOT_ASSIGNED()
        else:
            # NOTEX: fix collection nullable in daemon
            server_info = ServerAttributes(
                server_id, collection_id, revision_id, mailbox_server_id,
                mailbox_name, version, uid, thread_id, server_time, expunged)

        flags = jloads(flags)
        metadata = jloads(metadata)
        status, v = toInt(metadata.get("protocol_version"))
        if not status:
            raise EmailException(u"protocol_version must coerce to int")

        metadata.pop("protocol_version", None)

        metadata.update({
            "body": Content(
                block_ids=metadata["body"]["block_ids"],
                wrapped_key=metadata["body"]["wrapped_key"],
                key_version=metadata["body"]["key_version"]),
            "attachments": [
                Attachment.from_dict(att_dict)
                for att_dict in metadata.get("attachments")]
        })

        if v is PROTOCOL_VERSION.V1:
            return EmailV1(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V2:
            return EmailV2(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V3:
            return EmailV3(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V4:
            return EmailV4(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V5:
            return EmailV5(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V6:
            return EmailV6(**MergeDicts({"server_attr": server_info, "flags": flags}, metadata))

        raise EmailException(u"Unsupported protocol_version")

    @staticmethod  # noqa: C901
    @WrapExceptions(EmailException, [KeyError])
    @params(unicode, dict, unicode, int, {object, types.NoneType})  # TODO: give required props. in params
    def from_server_message(for_user_id, decrypted_msg, wrapped_key, key_version, mailbox):
        common_props = {
            "server_attr": ServerAttributes(
                decrypted_msg["id"], decrypted_msg["collection_id"],
                decrypted_msg["rev_id"], decrypted_msg["mailbox_id"],
                mailbox.name if mailbox else u"Unfetched", decrypted_msg["version"],
                decrypted_msg["uid"], decrypted_msg["thread_id"],
                decrypted_msg["timestamp"], decrypted_msg["is_deleted"]
            ),
            "flags": decrypted_msg["flags"],
            "sender": {
                "user_id": decrypted_msg["private_metadata"]["sender"],
                "display_name": decrypted_msg["private_metadata"]["sender"]
            },
            "subject": decrypted_msg["private_metadata"]["subject"],
            "message_id": decrypted_msg["message_id"],
            "in_reply_to": decrypted_msg["in_reply_to"],
            "references": decrypted_msg["references"],
            "reply_tos": [],
            "protocol_version": decrypted_msg["protocol_version"],
            "other_headers": decrypted_msg["private_metadata"].get("other_headers")
        }

        # protocol < 5
        protocol_dependent_props = {}
        if decrypted_msg["protocol_version"] <= PROTOCOL_VERSION.V4:
            body = Content(
                None, map(lambda b: b["id"], decrypted_msg["body"]["blocks"]),
                wrapped_key, key_version, decrypted_msg["body"]["size"])
            snippet = decrypted_msg["body"].get("snippet")
            attachments = [Attachment(
                AttachmentMetadata(att["name"], att["metadata"].get("content_type"), att["metadata"].get(
                    "content_disposition"), att["metadata"].get("content_id"), att["size"]),
                Content(
                    None, map(lambda b: b["id"], att["blocks"]), wrapped_key, key_version)
            ) for att in decrypted_msg["attachments"]]

            if decrypted_msg["protocol_version"] < PROTOCOL_VERSION.V4:
                tos = decrypted_msg["private_metadata"]["tos"]
                ccs = decrypted_msg["private_metadata"].get("ccs", [])
                bccs = decrypted_msg["private_metadata"].get("bccs", [])
            else:
                tos = map(lambda u: {"user_id": u, "display_name": u},
                          decrypted_msg["private_metadata"]["tos"])
                ccs = map(lambda u: {"user_id": u, "display_name": u},
                          decrypted_msg["private_metadata"].get("ccs", []))
                bccs = map(lambda u: {"user_id": u, "display_name": u},
                           decrypted_msg["private_metadata"].get("bccs", []))

        elif decrypted_msg["protocol_version"] >= PROTOCOL_VERSION.V5:
            body = Content(
                None, decrypted_msg["private_metadata"]["body"]["block_ids"],
                wrapped_key, key_version, decrypted_msg["private_metadata"]["body"]["size"])
            snippet = decrypted_msg["private_metadata"]["body"]["snippet"]
            attachments = [Attachment(
                AttachmentMetadata(att["name"], att["metadata"].get("content_type"), att["metadata"].get(
                    "content_disposition"), att["metadata"].get("content_id"), att["size"]),
                Content(None, att["block_ids"], wrapped_key, key_version)
            ) for att in decrypted_msg["private_metadata"]["attachments"]]

            tos = map(lambda r: EmailHelpers.format_recip(r),
                      decrypted_msg["private_metadata"]["tos"])
            ccs = map(lambda r: EmailHelpers.format_recip(r),
                      decrypted_msg["private_metadata"].get("ccs", []))

            # if sender, we can see all bccs
            # else figure out whether we are bcced.
            lfor_user_id = for_user_id.lower()
            if lfor_user_id == decrypted_msg["private_metadata"]["sender"].lower():
                bccs = map(lambda u: {"user_id": u["user_id"], "display_name": u["user_id"]},
                           decrypted_msg["private_metadata"].get("bccs", []))
            elif lfor_user_id not in [
                    recip["user_id"].lower()
                    for recip in decrypted_msg["private_metadata"]["tos"] +
                    decrypted_msg["private_metadata"]["ccs"] +
                    decrypted_msg["private_metadata"]["tos_groups"] +
                    decrypted_msg["private_metadata"]["ccs_groups"]
            ]:
                bccs = [{"user_id": for_user_id, "display_name": for_user_id}]
            else:
                # neither the sender or bcced, so cannot see the bccs
                bccs = []

        protocol_dependent_props = {
            "body": body,
            "snippet": snippet,
            "attachments": attachments,
            "tos": tos,
            "ccs": ccs,
            "bccs": bccs,
        }

        email_dict = MergeDicts(common_props, protocol_dependent_props)
        if decrypted_msg["protocol_version"] is PROTOCOL_VERSION.V1:
            return EmailV1(**email_dict)
        elif decrypted_msg["protocol_version"] is PROTOCOL_VERSION.V2:
            return EmailV2(**email_dict)
        elif decrypted_msg["protocol_version"] is PROTOCOL_VERSION.V3:
            return EmailV3(**email_dict)
        elif decrypted_msg["protocol_version"] is PROTOCOL_VERSION.V4:
            return EmailV4(**email_dict)
        elif decrypted_msg["protocol_version"] is PROTOCOL_VERSION.V5:
            return EmailV5(**email_dict)
        elif decrypted_msg["protocol_version"] is PROTOCOL_VERSION.V6:
            return EmailV6(**email_dict)

        raise EmailException("Unsupported protocol version {}".format(decrypted_msg["protocol_version"]))
