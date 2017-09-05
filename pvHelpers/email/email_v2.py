from .email_helpers import EmailHelpers, EmailException, PROTOCOL_VERSION
from .email_base import EmailBase
from ..misc import b64enc, g_log
import email.utils

class EmailV2(EmailHelpers, EmailBase):
    protocol_version = PROTOCOL_VERSION.V2

    def __init__(self, server_attr, flags, tos, ccs, bccs, sender, reply_tos, subject, \
                 body, attachments, references, in_reply_to, message_id, snippet=None):

        # check body content structure
        # if not isinstance(body, dict):
        #     raise EmailException(u"EmailV2.__init__: body must be of type dict")
        # if not isinstance(body.get("text"), unicode) or not isinstance(body.get("html"), unicode):
        #     raise EmailException(u"EmailV2.__init__: body['text']/body['html'] must exist and be of type unicode")

        super(EmailV2, self).__init__(server_attr, self.__class__.protocol_version, flags, \
                                      tos, ccs, bccs, sender, reply_tos, subject, \
                                      body,  attachments, references, in_reply_to, message_id, snippet)


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

    def toMIME(self):
        if not self.body.isLoaded() or ( len(self.attachments) > 0 and any([not attachment.isLoaded() for attachment in self.attachments])):
            raise EmailException(u"EmailV2.toMIME: All content must be loaded!")

        status, body = EmailHelpers.deserializeBody(self.body)
        if status == False:
            raise EmailException(u"EmailV2.toMIME: Failed to deserialize body")

        text = body.get("text")
        html = body.get("html")
        inline_attachments = filter(lambda att: att.metadata.content_disposition == u"inline" , self.attachments)
        regular_attachments = filter(lambda att: att.metadata.content_disposition != u"inline" , self.attachments)
        try:
            if html is None:
                if text == None:
                    text = u""
                body_shell = mime.create.text("plain", text)
            else:
                if inline_attachments:
                    html_part =  mime.create.multipart("related")
                    html_part.headers["Content-Type"].params["type"] = u"text/html"
                    html_text_part = mime.create.text("html", html)
                    html_part.append(html_text_part)
                    for att in inline_attachments:
                        html_part.append(att.toMIME())
                else:
                    html_part = mime.create.text("html", html)

                if text != None:
                    body_shell = mime.create.multipart("alternative")
                    body_shell.append(mime.create.text("plain", text), html_part)
                else:
                    body_shell = html_part

            if len(regular_attachments) > 0:
                message = mime.create.multipart("mixed")
                message.append(body_shell)
                for att in regular_attachments:
                    att_part = att.toMIME()
                    if att_part.content_type.is_message_container():
                        att_part.headers["Content-Type"].params["name"] = att.metadata.filename
                        att_part.headers["Content-Disposition"].params["filename"] = att.metadata.filename

                    message.append(att_part)
            else:
                message = body_shell

            message.headers["From"] = u"{} <{}>".format(self.sender["display_name"], self.sender["user_id"])
            if self.ccs:
                message.headers["Cc"] = u"{}".format(", ".join([u"{} <{}>".format(cc["display_name"], cc["user_id"]) for cc in self.ccs]))
            if self.tos:
                message.headers["To"] = u"{}".format(", ".join([u"{} <{}>".format(to["display_name"], to["user_id"]) for to in self.tos]))
            if self.bccs:
                message.headers["Bcc"] = u"{}".format(", ".join([u"{} <{}>".format(bcc["display_name"], bcc["user_id"]) for bcc in self.bccs]))
            if self.reply_to:
                message.headers["Reply-To"] = u"{}".format(", ".join([u"{} <{}>".format(rpt["display_name"], rpt["user_id"]) for rpt in self.reply_to]))

            if self.subject:
                message.headers["Subject"] = self.subject
            if self.message_id:
                message.headers["Message-Id"] = self.message_id
            if self.in_reply_to:
                message.headers["In-Reply-To"] = u"{}".format(self.in_reply_to)
            if self.references:
                message.headers["References"] = u"{}".format(" ".join(self.references))
            if self.server_attr.server_time:
                date = (u"%s" + u"\r\n") % email.utils.formatdate(self.server_attr.server_time)
                message.headers["Date"] = date

        except mime.EncodingError as e:
            raise EmailException(u"EmailV2.toMIME: exception, {}".format(e))

        return message

    # toBrowser is only to conform with browser expectations and can be removed
    def toBrowser(self, with_body=False):
        o = {}
        o["unique_id"] = self.server_attr.server_id
        o["uid"] = self.server_attr.uid
        o["thread_id"] = self.server_attr.thread_id
        o["mailbox_name"] = EmailHelpers.getMailboxAlias(self.server_attr.mailbox_name)
        o["mailbox_id"] = self.server_attr.mailbox_server_id
        o["snippet"] = self.snippet()
        o["flags"] = self.flags
        o["date"] = email.utils.formatdate(self.server_attr.server_time)
        o["subject"] = self.subject
        # This needs fixing, should get the names from server
        o["sender"] = {"address": self.sender["user_id"], "name": self.sender["display_name"]}
        o["tos"] = [{"address": to["user_id"], "name": to["display_name"]} for to in self.tos]
        o["ccs"] = [{"address": cc["user_id"], "name": cc["display_name"]} for cc in self.ccs]
        o["bccs"] = [{"address": bcc["user_id"], "name": bcc["display_name"]} for bcc in self.bccs]
        o["reply_to"] = [{"address": rpt["user_id"], "name": rpt["display_name"]} for rpt in self.reply_tos]
        o["in_reply_to"] = self.in_reply_to
        o["references"] = self.references

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
