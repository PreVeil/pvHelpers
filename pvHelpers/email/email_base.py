import types, copy
from .content import Content
from .attachment import Attachment
from .email_helpers import EmailException
from .server_attributes import ServerAttributes
from ..misc import NOT_ASSIGNED
#########################################
########### Factory Base Class ##########
#########################################
class EmailBase(object):
    __initialized = False
    def __init__(self, server_attr, protocol_version, flags, tos, ccs, bccs, sender, reply_tos, \
                 subject, body,  attachments, references, in_reply_to, message_id, snippet):
        if not isinstance(server_attr, (ServerAttributes, NOT_ASSIGNED)):
            raise EmailException(u"EmailBase.__init__: server_attr must be of type ServerAttributes/NOT_ASSIGNED")
        self.server_attr = server_attr

        if not isinstance(protocol_version, int):
            raise EmailException(u"EmailBase.__init__: protocol_version must be of type int")
        self.protocol_version = protocol_version

        if not isinstance(sender, dict):
            raise EmailException(u"EmailV1.__init__: sender must be of type dict")
        if not isinstance(sender.get("user_id"), unicode) or not isinstance(sender.get("display_name"), unicode):
            raise EmailException(u"EmailV1.__init__: sender['user_id']/sender['display_name'] must exist and be of type unicode")
        self.sender = sender

        if not isinstance(tos, list):
            raise EmailException(u"EmailV1.__init__: tos must be of type list")
        for to in tos:
            if not isinstance(to, dict):
                raise EmailException(u"EmailV1.__init__: tos element must be of type dict")
            if not isinstance(to.get("user_id"), unicode) or not isinstance(to.get("display_name"), unicode):
                raise EmailException(u"EmailV1.__init__: to['user_id']/to['display_name'] must exist and be of type unicode")
        self.tos = tos

        if not isinstance(ccs, list):
            raise EmailException(u"EmailV1.__init__: ccs must be of type list")
        for cc in ccs:
            if not isinstance(cc, dict):
                raise EmailException(u"EmailV1.__init__: ccs element must be of type dict")
            if not isinstance(cc.get("user_id"), unicode) or not isinstance(cc.get("display_name"), unicode):
                raise EmailException(u"EmailV1.__init__: cc['user_id']/cc['display_name'] must exist and be of type unicode")
        self.ccs = ccs

        if not isinstance(bccs, list):
            raise EmailException(u"EmailV1.__init__: bccs must be of type list")
        for bcc in bccs:
            if not isinstance(bcc, dict):
                raise EmailException(u"EmailV1.__init__: bccs element must be of type dict")
            if not isinstance(bcc.get("user_id"), unicode) or not isinstance(bcc.get("display_name"), unicode):
                raise EmailException(u"EmailV1.__init__: bcc['user_id']/bcc['display_name'] must exist and be of type unicode")
        self.bccs = bccs

        if not isinstance(reply_tos, list):
            raise EmailException(u"EmailV1.__init__: reply_tos must be of type list")
        self.reply_tos = []
        for rpt in reply_tos:
            if not isinstance(rpt, dict):
                continue
            if not isinstance(rpt.get("user_id"), unicode) or not isinstance(rpt.get("display_name"), unicode):
                continue
            self.reply_tos.append(rpt)

        if not isinstance(flags, list):
            raise EmailException(u"EmailBase.__init__: flags must be of type list")
        for flag in flags:
            if not isinstance(flag, unicode):
                raise EmailException(u"EmailBase.__init__: flags element must be of type unicode")
        self.flags = flags

        if not isinstance(subject, unicode):
            raise EmailException(u"EmailBase.__init__: subject must be of type unicode")
        self.subject = subject

        if not isinstance(body, Content):
            raise EmailException(u"EmailBase.__init__: body must be of type Content")
        self.body = body

        if not isinstance(attachments, list):
            raise EmailException(u"EmailBase.__init__: attachments must be of type list")
        for attachment in attachments:
            if not isinstance(attachment, Attachment):
                raise EmailException(u"EmailBase.__init__: bad attachment")
        self.attachments = attachments

        if not isinstance(in_reply_to, (unicode, types.NoneType)):
             raise EmailException(u"EmailBase.__init__: in_reply_to must be of type unicode")
        self.in_reply_to = in_reply_to

        if not isinstance(references, list):
            raise EmailException(u"EmailBase.__init__: references must be of type list")

        self.references = []
        for reference in references:
            if not isinstance(reference, unicode):
                # bad reference is fine, threading algo should work for the most part
                continue
            self.references.append(reference)

        if not isinstance(message_id, unicode):
            raise EmailException(u"EmailBase.__init__: message_id must be of type unicode")
        self.message_id = message_id

        if not isinstance(snippet, (unicode, types.NoneType)):
            raise EmailException(u"EmailBase.__init__: snippet must be of type unicode")
        self._snippet = snippet

        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"EmailBase has not attribute {}".format(key))
        object.__setattr__(self, key, value)

    def snippet(self):
        raise EmailException(NotImplemented(u"EmailBase.snippet: snippet getter not implemented"))

    def __deepcopy__(self, memo):
        return self.__class__(**copy.deepcopy(self.toDict()))

    def toBrowser(self):
        raise EmailException(NotImplemented(u"EmailBase.toBrowser: toBrowser must be implemented by children classes"))

    def toMime(self):
        raise EmailException(NotImplemented(u"EmailBase.toMime: toMime must be implemented by children classes"))

    def loadBody(self, content):
        self.body.content = content

    # def toDB(self):
    #     return {
    #         "server_id" : self.server_attr.server_id, "revision_id" : self.revision_id, "version" : self.server_attr.version,
    #         "flags" : H.jdumps(self.flags), "uid" : self.server_attr.uid,
    #         "expunged" : 1 if self.server_attr.expunged == True else 0, "mailbox_server_id" : self.server_attr.mailbox_server_id,
    #         "server_time" : self.server_attr.server_time, "thread_id" : self.server_attr.thread_id,
    #         "metadata": H.jdumps({
    #             "sender": self.sender,
    #             "tos": self.tos,
    #             "ccs": self.ccs,
    #             "bccs": self.bccs,
    #             "subject": self.subject,
    #             "attachments": [{"block_ids": attachment.content.block_ids, "reference_id": attachment.content.reference_id, "metadata": attachment.metadata.toDict()} for attachment in self.attachments],
    #             "message_id": self.message_id,
    #             "snippet": self.snippet(),
    #             "in_reply_to": self.in_reply_to,
    #             "references": self.references,
    #             "reply_tos": self.reply_tos,
    #             "protocol_version": self.protocol_version
    #         })
    #     }
