from .email import EmailException, PROTOCOL_VERSION, Content,\
                   EmailV1, EmailV2, EmailV3, EmailV4, ServerAttributes
from .misc import MergeDicts, NOT_ASSIGNED, jloads, toInt, g_log

#########################################
######### Email Entity Factory ##########
#########################################
class EmailFactory(object):
    @staticmethod
    def new(*args, **kwargs):
        v = kwargs.get("protocol_version", None)
        if v is None:
            raise EmailException(u"EmailFactory.__init__: Missing protocol_version named argument")
        kwargs.pop("protocol_version", None)

        if v is PROTOCOL_VERSION.V1:
            return EmailV1(*args, **kwargs)
        elif v is PROTOCOL_VERSION.V2:
            return EmailV2(*args, **kwargs)
        elif v is PROTOCOL_VERSION.V3:
            return EmailV3(*args, **kwargs)
        elif v is PROTOCOL_VERSION.V4:
            return EmailV4(*args, **kwargs)

        raise EmailException(u"EmailFactory.__init__: Unsupported protocol_version")

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

        # make content object and pass it
        metadata.update({
            "body": Content.fromDict(metadata.get("body")),
            "attachments": [Atttachment.fromDict(att_dict) for att_dict in metadata.get("attachments")]
        })

        if v is PROTOCOL_VERSION.V1:
            return EmailV1(MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V2:
            return EmailV2(MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V3:
            return EmailV3(MergeDicts({"server_attr": server_info, "flags": flags}, metadata))
        elif v is PROTOCOL_VERSION.V4:
            return EmailV4(MergeDicts({"server_attr": server_info, "flags": flags}, metadata))


        raise EmailException(u"EmailFactory.fromDict: Unsupported protocol_version")
