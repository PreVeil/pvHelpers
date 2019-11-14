import email.utils

from flanker import addresslib, mime
from pvHelpers.logger import g_log
from pvHelpers.utils import b64enc, EncodingException, NOT_ASSIGNED, params

from .base import EmailBase
from .content import Content
from .helpers import EmailException, EmailHelpers, PROTOCOL_VERSION
from .parsers import create_mime, parse_mime


class EmailV2(EmailHelpers, EmailBase):
    """Production version: Protocol version 2 is json based email entity"""
    protocol_version = PROTOCOL_VERSION.V2

    def __init__(self, server_attr, flags, tos, ccs, bccs, sender,
                 reply_tos, subject, body, attachments, references,
                 in_reply_to, message_id, snippet=None, other_headers=None, **kwargs):
        super(EmailV2, self).__init__(
            server_attr, self.__class__.protocol_version, flags,
            tos, ccs, bccs, sender, reply_tos, subject, body,
            attachments, references, in_reply_to, message_id, snippet)
        if body.content is not None:
            body = EmailHelpers.deserialize_body(body.content)
            if not isinstance(body, dict):
                raise EmailException(u"body must be of a serialized dict")
            if not isinstance(body.get("text"), unicode) or not isinstance(body.get("html"), unicode):
                raise EmailException(u"body['text']/body['html'] must exist and be of type unicode")

        self.other_headers = {} if other_headers is None else other_headers
        if not isinstance(self.other_headers, dict):
            raise EmailException(u"other_headers must be of type dict")

        self.__initialized = True

    def snippet(self):
        if self._snippet is None:
            body = EmailHelpers.deserialize_body(self.body.content)
            body_string = body.get("text")
            snippet = body_string[:1024]
            if len(body_string) > len(snippet):
                snippet += u"..."
            return snippet

        return self._snippet

    def to_mime(self):
        if not self.body.is_loaded() or \
           (len(self.attachments) > 0 and any([not attachment.is_loaded() for attachment in self.attachments])):
            raise EmailException(u"All content must be loaded!")

        body = EmailHelpers.deserialize_body(self.body.content)
        time = None
        if not isinstance(self.server_attr, NOT_ASSIGNED):
            time = self.server_attr.server_time

        raw_mime = create_mime(
            body["text"], body["html"], self.attachments, self.message_id, time, self.subject,
            self.tos, self.ccs, self.bccs, self.reply_tos, self.sender, self.in_reply_to, self.references)

        for key, value in self.other_headers.iteritems():
            raw_mime.headers[key] = value

        return mime.from_string(raw_mime.to_string())

    # is only to conform with browser expectations and can be removed
    def to_browser(self, with_body=False):
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
            if not self.body.is_loaded():
                body = {"text": u"", "html": u""}
            else:
                body = EmailHelpers.deserialize_body(self.body.content)

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

    def to_dict(self):
        return {
            "flags": self.flags,
            "snippet": self.snippet(),
            "subject": self.subject,
            "sender": self.sender,
            "tos": self.tos,
            "ccs": self.ccs,
            "bccs": self.bccs,
            "in_reply_to": self.in_reply_to,
            "reply_tos": self.reply_tos,
            "references": self.references,
            "attachments": self.attachments,
            "body": self.body,
            "message_id": self.message_id,
            "server_attr": self.server_attr,
            "other_headers": self.other_headers
        }

    # TODO: get tos ccs and ...
    @classmethod
    @params(object, bytes, [unicode], {"user_id": unicode, "display_name": unicode})
    def from_mime(cls, mime_string, flags, sender):
        named_sender = sender
        try:
            raw_mime = mime.create.from_string(mime_string)
        except mime.MimeError as e:
            raise EmailException(e)

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

        text, html, attachments = parse_mime(raw_mime)

        body = EmailHelpers.serialize_body({"text": text, "html": html})
        body = Content(body)

        return cls(NOT_ASSIGNED(), flags, named_tos, named_ccs, named_bccs,
                   named_sender, named_reply_tos, subject, body, attachments,
                   references, in_reply_to, message_id, other_headers=other_headers)
