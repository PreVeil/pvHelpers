from .email_helpers import EmailHelpers, EmailException, PROTOCOL_VERSION
from .email_base import EmailBase
from ..misc import b64enc, g_log, NOT_ASSIGNED
import email.utils
from .parsers import createMime

class EmailV2(EmailHelpers, EmailBase):
    protocol_version = PROTOCOL_VERSION.V2

    def __init__(self, server_attr, flags, tos, ccs, bccs, sender, reply_tos, subject, \
                 body, attachments, references, in_reply_to, message_id, snippet=None):
        super(EmailV2, self).__init__(server_attr, self.__class__.protocol_version, flags, \
                                      tos, ccs, bccs, sender, reply_tos, subject, \
                                      body,  attachments, references, in_reply_to, message_id, snippet)
        if body.content != None:
            status, body = EmailHelpers.deserializeBody(body.content)
            if status == False:
                raise EmailException(u"EmailV2.__init__: failed deserializing body")
            if not isinstance(body, dict):
                raise EmailException(u"EmailV2.__init__: body must be of a serialized dict")
            if not isinstance(body.get("text"), unicode) or not isinstance(body.get("html"), unicode):
                raise EmailException(u"EmailV2.__init__: body['text']/body['html'] must exist and be of type unicode")

    def snippet(self):
        if self._snippet is None:
            status, body = EmailHelpers.deserializeBody(self.body.content)
            if status == False:
                raise EmailException(u"EmailV2.snippet: Failed to deserialize body")

            body_string = body.get("text")
            snippet = body_string[:1024]
            if len(body_string) > len(snippet):
                snippet += u"..."
            return snippet

        return self._snippet

    def toMime(self):
        if not self.body.isLoaded() or (len(self.attachments) > 0 and any([not attachment.isLoaded() for attachment in self.attachments])):
            raise EmailException(u"EmailV2.toMime: All content must be loaded!")

        status, body = EmailHelpers.deserializeBody(self.body.content)
        if status == False:
            raise EmailException(u"EmailV2.toMime: Failed to deserialize body")

        time = None
        if not isinstance(self.server_attr, NOT_ASSIGNED):
            time = self.server_attr.server_time
        return createMime(body["text"], body["html"], self.attachments, self.message_id, time, self.subject, self.tos, self.ccs, self.bccs, self.reply_tos, self.sender, self.in_reply_to, self.references)

    # toBrowser is only to conform with browser expectations and can be removed
    def toBrowser(self, with_body=False):
        o = {}
        if not isinstance(self.server_attr, NOT_ASSIGNED):
            o["unique_id"] = self.server_attr.server_id
            o["uid"] = self.server_attr.uid
            o["thread_id"] = self.server_attr.thread_id
            o["mailbox_name"] = EmailHelpers.getMailboxAlias(self.server_attr.mailbox_name)
            o["mailbox_id"] = self.server_attr.mailbox_server_id
            o["date"] = email.utils.formatdate(self.server_attr.server_time)
        o["snippet"] = self.snippet()
        o["flags"] = self.flags
        o["subject"] = self.subject
        # This needs fixing, should get the names from server
        o["sender"] = {"address": self.sender["user_id"], "name": self.sender["display_name"]}
        o["tos"] = [{"address": to["user_id"], "name": to["display_name"]} for to in self.tos]
        o["ccs"] = [{"address": cc["user_id"], "name": cc["display_name"]} for cc in self.ccs]
        o["bccs"] = [{"address": bcc["user_id"], "name": bcc["display_name"]} for bcc in self.bccs]
        o["reply_to"] = [{"address": rpt["user_id"], "name": rpt["display_name"]} for rpt in self.reply_tos]
        o["in_reply_to"] = self.in_reply_to
        o["references"] = self.references
        o["message_id"] = self.message_id

        if with_body:
            if not self.body.isLoaded():
                body = {"text": u"", "html": u""}
            else:
                status, body = EmailHelpers.deserializeBody(self.body.content)
                if status == False:
                    raise EmailException(u"EmailV2.toBrowser: Failed to deserialize body")

            browser_atts = []
            for att in self.attachments:
                status, encoded = b64enc(att.content.content)
                if status == False:
                    continue

                browser_atts.append({
                    "filename": att.metadata.filename,
                    "content_type": att.metadata.content_type,
                    "size": len(att.content.content),
                    "content_disposition": att.metadata.content_disposition,
                    "content": encoded,
                    "content_id": att.metadata.content_id,
                })

            o["html"] = body.get("html")
            o["text"] = body.get("text")
            o["attachments"] = browser_atts
        else:
            o["html"] = None
            o["text"] = None
            o["attachments"] = [{
                "filename": att.metadata.filename,
                "content_type": att.metadata.content_type,
                "size": None,
                "content": None,
                "content_disposition": att.metadata.content_disposition,
                "content_id": att.metadata.content_id
            } for att in self.attachments]

        return o

    def toDict(self):
        return {
            "flags": self.flags,
            "subject": self.subject,
            "sender": self.sender,
            "tos": self.tos,
            "ccs": self.ccs,
            "bccs" : self.bccs,
            "in_reply_to" : self.in_reply_to,
            "reply_tos": self.reply_tos,
            "references" : self.references,
            "attachments" : self.attachments,
            "body": self.body,
            "message_id": self.message_id,
            "server_attr": self.server_attr
        }
