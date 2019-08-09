from .email_helpers import EmailHelpers, EmailException, PROTOCOL_VERSION
from .email_base import EmailBase
from ..misc import b64enc, g_log, NOT_ASSIGNED, EncodingException
from pvHelpers.hook_decorators import WrapExceptions
import email.utils
from .parsers import createMime, parseMime
from flanker import mime, addresslib
from .content import Content

class EmailV2(EmailHelpers, EmailBase):
    """Production version: Protocol version 2 is json based email entity"""
    protocol_version = PROTOCOL_VERSION.V2

    def __init__(self, server_attr, flags, tos, ccs, bccs, sender, reply_tos, subject, \
                 body, attachments, references, in_reply_to, message_id, snippet=None, other_headers=None, **kwargs):
        super(EmailV2, self).__init__(server_attr, self.__class__.protocol_version, flags, \
                                      tos, ccs, bccs, sender, reply_tos, subject, \
                                      body,  attachments, references, in_reply_to, message_id, snippet)
        if body.content != None:
            body = EmailHelpers.deserializeBody(body.content)
            if not isinstance(body, dict):
                raise EmailException(u"EmailV2.__init__: body must be of a serialized dict")
            if not isinstance(body.get("text"), unicode) or not isinstance(body.get("html"), unicode):
                raise EmailException(u"EmailV2.__init__: body['text']/body['html'] must exist and be of type unicode")

        self.other_headers = {} if other_headers is None else other_headers
        if not isinstance(self.other_headers, dict):
            raise EmailException(u"EmailV2.__init__: other_headers must be of type dict")

        self.__initialized = True

    def snippet(self):
        if self._snippet is None:
            body = EmailHelpers.deserializeBody(self.body.content)
            body_string = body.get("text")
            snippet = body_string[:1024]
            if len(body_string) > len(snippet):
                snippet += u"..."
            return snippet

        return self._snippet

    def toMime(self):
        if not self.body.isLoaded() or (len(self.attachments) > 0 and any([not attachment.isLoaded() for attachment in self.attachments])):
            raise EmailException(u"EmailV2.toMime: All content must be loaded!")

        body = EmailHelpers.deserializeBody(self.body.content)
        time = None
        if not isinstance(self.server_attr, NOT_ASSIGNED):
            time = self.server_attr.server_time

        raw_mime = createMime(body["text"], body["html"], self.attachments, self.message_id, time, self.subject, self.tos, self.ccs, self.bccs, self.reply_tos, self.sender, self.in_reply_to, self.references)

        for key, value in self.other_headers.iteritems():
            raw_mime.headers[key] = value

        return mime.from_string(raw_mime.to_string())

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
            o["rev_id"] = self.server_attr.revision_id
            o["is_local"] = EmailHelpers.isLocalEmail(self.server_attr.server_id)
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
                body = EmailHelpers.deserializeBody(self.body.content)

            browser_atts = []
            for att in self.attachments:
                try:
                    encoded = b64enc(att.content.content)
                except EncodingException as e:
                    g_log.exception(e)
                    continue

                browser_atts.append({
                    "filename": att.metadata.filename,
                    "content_type": att.metadata.content_type,
                    "size": att.metadata.size,
                    "content_disposition": att.metadata.content_disposition,
                    "content_reference_id": att.content.reference_id,
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
                "size": att.metadata.size,
                "content_reference_id": att.content.reference_id,
                "content": None,
                "content_disposition": att.metadata.content_disposition,
                "content_id": att.metadata.content_id
            } for att in self.attachments]

        return o

    def toDict(self):
        return {
            "flags": self.flags,
            "snippet": self.snippet(),
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
            "server_attr": self.server_attr,
            "other_headers": self.other_headers
        }

    #TODO: get tos ccs and ...
    @classmethod
    def fromMime(cls, mime_string, flags, sender):
        if not isinstance(mime_string, (str, bytes)):
            raise EmailException(u"EmailV1.fromMime: mime_string must be of type str/bytes")

        if not isinstance(sender, dict):
            raise EmailException(u"EmailV1.fromMime: sender must be of type dict")
        if not isinstance(sender.get("user_id"), unicode) or not isinstance(sender.get("display_name"), unicode):
            raise EmailException(u"EmailV1.fromMime: sender['user_id']/sender['display_name'] must exist and be of type unicode")

        named_sender = sender

        try:
            raw_mime = mime.create.from_string(mime_string)
        except mime.MimeError as e:
            raise EmailException(u"EmailV1.fromMime: flanker exception {}".format(e))

        message_id = raw_mime.headers.get("Message-Id")

        tos = raw_mime.headers.get("To")
        tos = addresslib.address.parse_list(tos)
        named_tos = [{"user_id": to.address, "display_name": to.display_name} for to in tos]
        ccs = raw_mime.headers.get("Cc")
        ccs = addresslib.address.parse_list(ccs)
        named_ccs = [{"user_id": cc.address, "display_name": cc.display_name} for cc in ccs]
        bccs = raw_mime.headers.get("Bcc")
        bccs = addresslib.address.parse_list(bccs)
        named_bccs = [{"user_id": bcc.address, "display_name": bcc.display_name} for bcc in bccs]
        reply_to = raw_mime.headers.get("Reply-To")
        reply_tos = addresslib.address.parse_list(reply_to)
        named_reply_tos = [{"user_id": rpt.address, "display_name": rpt.display_name} for rpt in reply_tos]

        references = [u"<{}>".format(ref) for ref in raw_mime.references]
        in_reply_to = raw_mime.headers.get("In-Reply-To", None)
        subject = raw_mime.headers.get("Subject", u"")

        other_headers = {}
        for key, value in raw_mime.headers.iteritems():
            if key.startswith("X-"):
                # str(value)?
                other_headers[key] = value

        text, html, attachments = parseMime(raw_mime)

        body = EmailHelpers.serializeBody({"text": text, "html":html})
        body = Content(body)

        return cls(NOT_ASSIGNED(), flags, named_tos, named_ccs, named_bccs, named_sender, \
                   named_reply_tos, subject, body, attachments, references, in_reply_to, message_id, other_headers=other_headers)
