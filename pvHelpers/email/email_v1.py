from .email_helpers import EmailHelpers, EmailException, PROTOCOL_VERSION, DUMMY_DISPOSITION, DUMMY_CONTENT_TYPE
from .email_base import EmailBase
from ..misc import MergeDicts, b64enc, NOT_ASSIGNED, g_log
from flanker import mime, addresslib
from .attachment import Attachment, AttachmentMetadata
from .content import Content
import email.utils, types, libnacl
from .parsers import parseMime
from ..keys import sha256

# Using this with the flanker MIME class forces it to always reparse the
# entire object before outputting it in the to_string() method.  This is
# useful when we modify the objects internals thru an unsanctioned interface.
def was_changed_always(self, ignore_prepends=False):
    return True

class EmailV1(EmailHelpers, EmailBase):
    """Production version: Protocol version 1 is mime based email entity"""
    protocol_version = PROTOCOL_VERSION.V1

    def __init__(self, server_attr, flags, tos, ccs, bccs, sender, reply_tos, subject, \
                 body, attachments, references, in_reply_to, message_id, snippet=None, **kwargs):

        super(EmailV1, self).__init__(server_attr, self.__class__.protocol_version, flags, tos, \
                                      ccs, bccs, sender, reply_tos, subject, body, \
                                      attachments, references, in_reply_to, message_id, snippet)
        # TODO: check body content mime validity


        self.__initialized = True

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

            message_body, att_parts = EmailV1.separateAttachments(raw_mime)
            body = message_body.to_string()
            body = Content(body, None, None)
            attachments = []
            for att_part in att_parts:
                t, o = att_part.content_disposition
                filename = o.get("filename")
                if filename is None:
                    filename = u"untitled"
                metadata = AttachmentMetadata(filename, u"{}/{}".format(att_part.content_type.main, att_part.content_type.sub), t, None)
                content = Content(att_part.to_string(), None, None)
                attachments.append(Attachment(metadata, content))
        except mime.MimeError as e:
            raise EmailException(u"EmailV1.fromMime: flanker exception {}".format(e))

        return cls(NOT_ASSIGNED(), flags, named_tos, named_ccs, named_bccs, named_sender, \
                   named_reply_tos, subject, body, attachments, references, in_reply_to, message_id)

    @staticmethod
    def convertStringToMime(message):
        if not isinstance(message, (str, bytes)):
            raise EmailException(TypeError(u"message must be of type str/bytes"))

        try:
            return mime.create.from_string(message)
        except mime.MimeError as e:
            raise EmailException(u"EmailV1.convertStringToMime: flanker exception {}".format(e))

    @staticmethod
    def separateAttachments(msg):
        msg = mime.create.from_string(msg.to_string())
        if msg.content_type.is_multipart():
            # An email is a tree consisting of interior nodes, which have
            # Content-Type: multipart/*, and leaf nodes (bodies, attachments)
            new_parts = []
            attachments = []
            for p in msg.parts:
                new_p, atts = EmailV1.separateAttachments(p)
                new_parts.append(new_p)
                attachments += atts
            msg.parts = new_parts
            # HACK: Must be set on the MIMEPart that has been modified
            msg.was_changed = types.MethodType(was_changed_always, msg)
            return msg, attachments

        t, o = msg.content_disposition
        if t not in ("attachment", "inline"):
            return msg, []
        else:
            status, att_hash = sha256(msg.to_string())
            if status == False:
                raise EmailException(u"Failed to hash msg")
            # Insert a dummy node into the message tree so we know where to insert
            # this attachment when reconstructing the email
            placeholder = mime.create.attachment(DUMMY_CONTENT_TYPE, u"placeholder for an attachment", filename=att_hash, disposition=DUMMY_DISPOSITION)
            return placeholder, [msg]

    @staticmethod
    def restoreAttachments(msg, atts):
        if msg.content_type.is_multipart():
            new_parts = []
            for x in msg.parts:
                status, new_part = EmailV1.restoreAttachments(x, atts)
                if status == False:
                    return False, None
                new_parts.append(new_part)
            msg.parts = new_parts
            # HACK: Must be set on the MIMEPart that has been modified
            msg.was_changed = types.MethodType(was_changed_always, msg)
            return True, msg
        if msg.content_type == DUMMY_CONTENT_TYPE:
            t, o = msg.content_disposition
            att_id = o.get("filename")
            if att_id is None or att_id not in atts:
                return False, None
            return True, atts[att_id]
        else:
            return True, msg

    @staticmethod
    def replaceDummyReferences(message, reference_map):
        if not isinstance(message, mime.message.part.MimePart):
            return False, None
        for part in message.walk(with_self=True):
            if part.content_type == DUMMY_CONTENT_TYPE:
                t, o = part.content_disposition
                filename = o.get("filename")
                if filename in reference_map:
                    part.content_disposition.params["filename"] = reference_map[filename]
                # HACK: Must be set on the MIMEPart that has been modified
                part.was_changed = types.MethodType(was_changed_always, part)
        message.was_changed = types.MethodType(was_changed_always, message)
        return True, mime.from_string(message.to_string())

    @staticmethod
    def setMIMEBcc(message, bccs):
        if not isinstance(message, mime.message.part.MimePart):
            return False, None
        if not isinstance(bccs, list):
            return False, None
        for bcc in bccs:
            if not isinstance(bcc, dict):
                return False, None
            if not isinstance(bcc.get("user_id"), unicode) or not isinstance(bcc.get("display_name"), unicode):
                return False, None

        if len(bccs) == 0:
            message.remove_headers("Bcc")
        else:
            message.headers["Bcc"] = u"{}".format(", ".join([u"{} <{}>".format(bcc["display_name"], bcc["user_id"]) for bcc in bccs]))

        return True, mime.from_string(message.to_string())

    def snippet(self):
        if self._snippet is None:
            raw_mime = self.toMime()

            plain_string = None
            # only using plain/text parts for snippet generation.
            # TODO: add a HTML stripper and use plain/html parts if
            # there are no plain/text alternatives
            for part in raw_mime.walk(with_self=True):
                if part.content_type == "text/plain":
                    if plain_string is None:
                        plain_string = part.body
                    else:
                        plain_string += u"\n" + part.body

            if plain_string is None:
                return u""

            snippet = plain_string[:1024]
            if len(plain_string) > len(snippet):
                snippet += u"..."

            return snippet

        return self._snippet

    def toMime(self):
        if not self.body.isLoaded() or (len(self.attachments) > 0 and any([not attachment.isLoaded() for attachment in self.attachments])):
            raise EmailException(u"EmailV1.toMime: All content must be loaded!")

        try:
            status, message = EmailV1.restoreAttachments(mime.create.from_string(self.body.content), {libnacl.encode.hex_encode(libnacl.crypto_hash_sha256(att.content.content)): mime.create.from_string(att.content.content) for att in self.attachments})
            if status == False:
                raise EmailException(u"EmailV1.toMime: failed to restore atts")
            # Reporting the server reception time,
            # 1) similar to what we report to browser,
            # 2) Dates added by MUAs can be incorrect
            if not isinstance(self.server_attr, NOT_ASSIGNED) and self.server_attr.server_time != None:
                date = (u"%s" + u"\r\n") % email.utils.formatdate(self.server_attr.server_time)
                message.headers["Date"] = date

        except mime.MimeError as e:
            raise EmailException(u"toMime: flanker exception {}".format(e))

        return message

    def toBrowser(self, with_body=False):
        # check loaded!?
        o = {}
        if not isinstance(self.server_attr, NOT_ASSIGNED):
            o["unique_id"] = self.server_attr.server_id
            o["uid"] = self.server_attr.uid
            o["thread_id"] = self.server_attr.thread_id
            o["mailbox_name"] = EmailHelpers.getMailboxAlias(self.server_attr.mailbox_name)
            o["mailbox_id"] = self.server_attr.mailbox_server_id
            o["date"] = email.utils.formatdate(self.server_attr.server_time)
        o["flags"] = self.flags
        o["snippet"] = self.snippet()
        o["subject"] = self.subject
        # THis needs fixing, get names from server
        o["sender"] = {"address": self.sender["user_id"], "name": self.sender["display_name"]}
        o["tos"] = [{"address": to["user_id"], "name": to["display_name"]} for to in self.tos]
        o["ccs"] = [{"address": cc["user_id"], "name": cc["display_name"]} for cc in self.ccs]
        o["bccs"] = [{"address": bcc["user_id"], "name": bcc["display_name"]} for bcc in self.bccs]
        o["reply_to"] = [{"address": rpt["user_id"], "name": rpt["display_name"]} for rpt in self.reply_tos]
        o["in_reply_to"] = self.in_reply_to
        o["references"] = self.references
        o["message_id"] = self.message_id

        if with_body:
            try:
                message = self.toMime()
                o["text"], o["html"], attachments = parseMime(message)
            except mime.MimeError as e:
                raise EmailException(u"EmailV1.toBrowser: exception {}".format(e))

            browser_atts = []
            for att in attachments:
                status, encoded = b64enc(att.content.content)
                if status == False:
                    continue

                browser_atts.append({
                    "filename": att.metadata.filename,
                    "content_type": att.metadata.content_type,
                    "size": att.metadata.size,
                    "content_disposition": att.metadata.content_disposition,
                    "content": encoded,
                    "content_id": att.metadata.content_id
                })

            o["attachments"] = browser_atts
        else:
            o["html"] = None
            o["text"] = None
            o["attachments"] = [{
                "filename": att.metadata.filename,
                "content_type": att.metadata.content_type,
                "size": att.metadata.size,
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
