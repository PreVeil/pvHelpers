import uuid
import types
import email.utils
from flanker import mime, addresslib
from . import misc
from werkzeug.datastructures import FileStorage
import copy
import libnacl

DUMMY_DISPOSITION = u"dummy"
DUMMY_CONTENT_TYPE = u"dummy/dummy"

class PROTOCOL_VERSION():
    V1 = 1
    V2 = 2

class EmailException(Exception):
    def __init__(self, message=u""):
        Exception.__init__(self, message)

class AttachmentMetadata(object):
    def __init__(self, filename=None, content_type=None, content_disposition=u"attachment", content_id=None, block_ids=None):
        if isinstance(filename, str):
            status, filename = misc.ASCIIToUnicode(filename)
            if status == False:
                raise EmailException(u"AttachmentMetadata.__init__: failed to convert filename to unicode")
        if not isinstance(filename, (unicode, types.NoneType)):
            raise EmailException(u"AttachmentMetadata.__init__: filename must be unicode, {}".format(filename))
        self.filename = filename

        if isinstance(content_type, str):
            status, content_type = misc.ASCIIToUnicode(content_type)
            if status == False:
                raise EmailException(u"AttachmentMetadata.__init__: failed to convert content_type to unicode")
        if not isinstance(content_type, (unicode, types.NoneType)):
            raise EmailException(u"AttachmentMetadata.__init__:: content_type must be of type unicode, {}".format(content_type))

        if content_type is None:
            self.content_type = u"application/octet-stream"
        else:
            self.content_type = content_type

        # if we don't specify this, flanker will default to (c-d= attachment)  or (c-d=None) if no filename available
        # defaulting to attachment so that we always return the raw content regardless,
        # and keep it MIME consistent with object
        content_disposition = u"attachment" if content_disposition is None else content_disposition
        if isinstance(content_disposition, str):
            status, content_disposition = misc.ASCIIToUnicode(content_disposition)
            if status == False:
                raise EmailException(u"AttachmentMetadata.__init__: failed to convert content_disposition to unicode")
        if not isinstance(content_disposition, unicode):
            raise EmailException(u"AttachmentMetadata.__init__: content_disposition must be unicode, value: {}".format(content_disposition))
        self.content_disposition = content_disposition

        if isinstance(content_id, str):
            status, content_id = misc.ASCIIToUnicode(content_id)
            if status == False:
                raise EmailException(u"AttachmentMetadata.__init__: failed to convert content_id to unicode")
        if not isinstance(content_id, (unicode, types.NoneType)):
            raise EmailException(u"AttachmentMetadata.__init__: content_id must be unicode, value: {}".format(content_id))
        self.content_id = content_id

        if not isinstance(block_ids, (list, types.NoneType)):
            raise EmailException(u"AttachmentMetadata.__init__: block_ids must be list, value: {}".format(content_id))
        self.block_ids = block_ids

    def toDict(self):
        return {
            "filename" : self.filename,
            "content_type" : self.content_type,
            "content_disposition" : self.content_disposition,
            "content_id" : self.content_id,
            "block_ids": self.block_ids
        }

class Attachment(object):
    @staticmethod
    def fromFileStorage(_file):
        content = _file.read()
        status, content = Email.encodeContentIfUnicode(content)
        if status == False:
            raise EmailException(u"fromFileStorage: Failed to encode content")
        # flanker defaults the mime header to (application/octet-stream) if c-t not specified
        # it also makes some assumptions based on filename if c-t is (application/octet-stream)
        # so keeping our object consistent with the MIME which is going to be generated
        try:
            main, sub = mime.message.headers.parametrized.fix_content_type(_file.content_type, default=(u"application", u"octet-stream"))
            content_type = mime.message.part.adjust_content_type(mime.message.ContentType(main, sub),  content, _file.filename)
        except mime.MimeError as e:
            raise EmailException(u"fromFileStorage: flanker exception, value: {}".format(e))

        status, content_type = misc.unicodeIfUnicodeElseDecode(_file.content_type)
        if status == False:
            raise EmailException(u"fromFileStorage: content_type str to unicode failed")

        return Attachment(None, AttachmentMetadata(_file.filename, content_type), content)

    @staticmethod
    def fromDict(data):
        metadata = data.get("metadata")
        metadata = AttachmentMetadata(metadata.get("filename"), metadata.get("content_type"), metadata.get("content_disposition"), metadata.get("content_id"), metadata.get("block_ids"))

        content = data.get("content", None)
        reference_id = data.get("reference_id", None)

        if reference_id == None and content == None:
            raise EmailException(u"Attachment.fromDict: attachment must have content!")

        return Attachment(reference_id, metadata, content)

    # should use Email.fromDict() unless certain about types
    def __init__(self, reference_id, metadata, content):
        if not isinstance(reference_id, (unicode, types.NoneType)):
            raise EmailException(u"__init__: Bad reference_id, value: {}".format(reference_id))
        self.reference_id = reference_id

        if not isinstance(content, (str, bytes, types.NoneType)):
            raise EmailException(u"__init__: Bad content, reference_id: {}".format(reference_id))
        self.content = content

        if content is None and reference_id is None:
            raise EmailException(u"__init__: must have either content or ref_id")

        if not isinstance(metadata, AttachmentMetadata):
            raise EmailException(u"__init__: bad metadata, value: {}".format(metadata))
        self.metadata = metadata

    def loadContent(self, content):
        self.content = content

    def toMIME(self):
        if self.content is None:
            raise EmailException(u"toMIME: content must be loaded")
        try:
            part = mime.create.attachment(content_type=self.metadata.content_type, body=self.content, filename=self.metadata.filename, disposition=self.metadata.content_disposition)
            if self.metadata.content_id:
                part.headers["Content-Id"] = self.metadata.content_id
        except mime.EncodingError as e:
            raise EmailException(u"toMIME: flanker exception, {}".format(e))
        return part

    def toDict(self):
        return {
            "reference_id" : self.reference_id,
            "content" : self.content,
            "metadata" : self.metadata.toDict()
        }

class Email(object):
    @staticmethod
    def getSnippetFromMIME(raw_mime):
        if not isinstance(raw_mime, mime.message.part.MimePart):
            raise EmailException(u"getSnippetFromMIME: raw_mime must be of type MimePart")

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

    @staticmethod
    def getSnippetFromText(body_string):
        if not isinstance(body_string, (str, unicode)):
            raise EmailException(u"getSnippetFromText: body_string must be of type str/unicode")
        snippet = body_string[:1024]
        if len(body_string) > len(snippet):
            snippet += u"..."
        return snippet

    @staticmethod
    def encodeContentIfUnicode(content):
        if isinstance(content, unicode):
            return misc.utf8Encode(content)
        return True, content

    @staticmethod
    def newMessageId():
        return u"{}@preveil.com".format(str(uuid.uuid4()))

    @staticmethod
    def fromDB(revision_id, version, server_id, metadata, server_time, flags, uid, mailbox_server_id, thread_id, mailbox_name):
        status, flags = misc.jloads(flags)
        if status == False:
            raise EmailException(u"fromDB: bad flags json")

        status, metadata = misc.jloads(metadata)
        if status == False:
            raise EmailException(u"fromDB: bad metadata json")

        status, protocol_version = misc.toInt(metadata.get("protocol_version"))
        if status == False:
            raise EmailException(u"fromDB: protocol_version must coerce to int")

        return Email.fromDict({
            "revision_id": revision_id,
            "expunged": False,
            "version": version,
            "server_id": server_id,
            "server_time": server_time,
            "flags": flags,
            "uid": uid,
            "mailbox_server_id": mailbox_server_id,
            "thread_id": thread_id,
            "mailbox_name": mailbox_name,
            "body_ref_id": metadata.get("body_ref_id"),
            "sender": metadata.get("sender"),
            "tos": metadata.get("tos"),
            "ccs": metadata.get("ccs"),
            "bccs": metadata.get("bccs"),
            "subject": metadata.get("subject"),
            "attachments": metadata.get("attachments"),
            "message_id": metadata.get("message_id"),
            "snippet": metadata.get("snippet"),
            "in_reply_to": metadata.get("in_reply_to"),
            "references": metadata.get("references"),
            "reply_to": metadata.get("reply_to"),
            "protocol_version": protocol_version
        })

    @staticmethod
    def fromDict(data):
        if not isinstance(data, dict):
            raise EmailException(u"fromDict: data must be of type dict")
        sender = data.get("sender")
        tos = data.get("tos", [])
        ccs = data.get("ccs", [])
        bccs = data.get("bccs", [])
        reply_to = data.get("reply_to", [])
        flags = data.get("flags", [])
        subject = data.get("subject", u"")
        in_reply_to = data.get("in_reply_to", None)
        references = data.get("references", [])
        atts = data.get("attachments", [])
        message_id = data.get("message_id", None)
        body_ref_id = data.get("body_ref_id", None)
        body = data.get("body", None)

        if body_ref_id == None and body == None:
            raise EmailException(u"fromDict: email must have body content!")

        if not isinstance(atts, list):
            raise EmailException(u"fromDict: attachments must be of type list")

        attachments = []
        for att in atts:
            if isinstance(att, Attachment):
                attachment = att
            elif isinstance(att, dict):
                attachment = Attachment.fromDict(att)
            elif isinstance(att, FileStorage):
                attachment = Attachment.fromFileStorage(att)
            else:
                raise EmailException(u"fromDict: Attachment type not supported")

            attachments.append(attachment)

        # below are the fields that new sending emails won't have.
        server_id = data.get("server_id", None)
        mailbox_server_id = data.get("mailbox_server_id", None)
        mailbox_name = data.get("mailbox_name", None)
        revision_id = data.get("revision_id", None)
        version = data.get("version", None)
        uid = data.get("uid", None)
        thread_id = data.get("thread_id", None)
        snippet = data.get("snippet", u"")
        if snippet is None:
            snippet = u""
        expunged = data.get("expunged", None)
        server_time = data.get("server_time", None)
        protocol_version = data.get("protocol_version", None)

        return Email(server_id, uid, thread_id, mailbox_server_id, mailbox_name, \
                        version, snippet, message_id, references, protocol_version, \
                        in_reply_to, attachments, body, body_ref_id, subject, \
                        flags, tos, ccs, bccs, sender, expunged, server_time, revision_id, reply_to)

    @staticmethod # raw mime only has some of an email information like body, atts, ...
    def fromMIME(raw_mime, server_id, revision_id, protocol_version, version, \
                    snippet, uid, thread_id, mailbox_server_id, flags, message_id, \
                    server_time, subject, sender, tos, ccs, bccs, reply_to, in_reply_to, references, expunged):
        if not isinstance(raw_mime, mime.message.part.MimePart):
            raise EmailException(u"fromMIME: raw_mime must be of type mime.message.part.MimePart or str")

        if tos == None:
            tos = raw_mime.headers.get("To")
            tos = addresslib.address.parse_list(tos)
            tos = [{"user_id": to.address, "display_name": to.display_name} for to in tos]
        if ccs == None:
            ccs = raw_mime.headers.get("Cc")
            ccs = addresslib.address.parse_list(ccs)
            ccs = [{"user_id": cc.address, "display_name": cc.display_name} for cc in ccs]
        if bccs == None:
            bccs = raw_mime.headers.get("Bcc")
            bccs = addresslib.address.parse_list(bccs)
            bccs = [{"user_id": bcc.address, "display_name": bcc.display_name} for bcc in bccs]
        if reply_to == None:
            reply_to = raw_mime.headers.get("Reply-To")
            reply_to = addresslib.address.parse_list(reply_to)
            reply_to = [{"user_id": rpt.address, "display_name": rpt.display_name} for rpt in reply_to]
        if subject == None:
            subject = raw_mime.headers.get("Subject", u"")
        if in_reply_to == None:
            in_reply_to = raw_mime.headers.get("In-Reply-To")
        if references == None:
            references = [u"<{}>".format(ref) for ref in raw_mime.references]
        if message_id == None:
            message_id = raw_mime.headers.get("Message-Id")

        if protocol_version == PROTOCOL_VERSION.V1:
            try:
                message_body, att_parts = _separateAttachments(raw_mime)
                body = message_body.to_string()
                mime_snippet = Email.getSnippetFromMIME(raw_mime)
                attachments = []
                for att_part in att_parts:
                    t, o = att_part.content_disposition
                    filename = o.get("filename")
                    if filename is None:
                        filename = u"untitled"
                    attachments.append({
                        "metadata": {
                            "filename": filename,
                            "content_type": u"{}/{}".format(att_part.content_type.main, att_part.content_type.sub),
                            "content_disposition": t
                        },
                        "content": att_part.to_string()
                    })
            except mime.MimeError as e:
                raise EmailException(u"fromMIME: separation flanker exception {}".format(e))

        elif protocol_version == PROTOCOL_VERSION.V2:
            try:
                text, html, attachments = _parseMIME(raw_mime)
                mime_snippet = Email.getSnippetFromText(text)
                status, body = Email.serializeBody({"text": text, "html": html})
                if status == False:
                    raise EmailException(u"parseMIME: failed to serialize")
            except mime.MimeError as e:
                raise EmailException(u"fromMIME: parsing flanker exception {}".format(e))

        else:
            raise EmailException(u"fromMIME: protocol_version not supported")

        if snippet is None:
            snippet = mime_snippet

        return Email.fromDict({
            "server_id": server_id,
            "expunged": expunged,
            "revision_id": revision_id,
            "protocol_version": protocol_version,
            "version": version,
            "snippet": snippet,
            "uid": uid,
            "thread_id": thread_id,
            "mailbox_server_id": mailbox_server_id,
            "flags": flags,
            "message_id": message_id,
            "server_time": server_time,
            "subject": subject,
            "sender": sender,
            "tos": tos,
            "ccs": ccs,
            "bccs" : bccs,
            "reply_to": reply_to,
            "in_reply_to" : in_reply_to,
            "references" : references,
            "attachments" : attachments,
            "body" : body,
            "protocol_version": protocol_version
        })

    # should use fromDict(), or fromMIME() staticmethods
    def __init__(self, server_id, uid, thread_id, mailbox_server_id, mailbox_name, \
                version, snippet, message_id, references, protocol_version, \
                in_reply_to, attachments, body, body_ref_id, subject, flags, tos, \
                ccs, bccs, sender, expunged, server_time, revision_id, reply_to):

        if not isinstance(sender, dict):
            raise EmailException(u"Email.__init__: sender must be of type dict")
        if not isinstance(sender.get("user_id"), unicode) or not isinstance(sender.get("display_name"), unicode):
            raise EmailException(u"Email.__init__: sender['user_id']/sender['display_name'] must exist and be of type unicode")
        self.sender = sender

        if not isinstance(tos, list):
            raise EmailException(u"Email.__init__: tos must be of type list")
        for to in tos:
            if not isinstance(to, dict):
                raise EmailException(u"Email.__init__: tos element must be of type dict")
            if not isinstance(to.get("user_id"), unicode) or not isinstance(to.get("display_name"), unicode):
                raise EmailException(u"Email.__init__: to['user_id']/to['display_name'] must exist and be of type unicode")
        self.tos = tos

        if not isinstance(ccs, list):
            raise EmailException(u"Email.__init__: ccs must be of type list")
        for cc in ccs:
            if not isinstance(cc, dict):
                raise EmailException(u"Email.__init__: ccs element must be of type dict")
            if not isinstance(cc.get("user_id"), unicode) or not isinstance(cc.get("display_name"), unicode):
                raise EmailException(u"Email.__init__: cc['user_id']/cc['display_name'] must exist and be of type unicode")
        self.ccs = ccs

        if not isinstance(bccs, list):
            raise EmailException(u"Email.__init__: bccs must be of type list")
        for bcc in bccs:
            if not isinstance(bcc, dict):
                raise EmailException(u"Email.__init__: bccs element must be of type dict")
            if not isinstance(bcc.get("user_id"), unicode) or not isinstance(bcc.get("display_name"), unicode):
                raise EmailException(u"Email.__init__: bcc['user_id']/bcc['display_name'] must exist and be of type unicode")
        self.bccs = bccs

        if not isinstance(reply_to, list):
            raise EmailException(u"Email.__init__: reply_to must be of type list")
        self.reply_to = []
        for rep in reply_to:
            if not isinstance(rep, dict):
                continue
            if not isinstance(rep.get("user_id"), unicode) or not isinstance(rep.get("display_name"), unicode):
                continue
            self.reply_to.append(rep)

        if not isinstance(flags, list):
            raise EmailException(u"Email.__init__: flags must be of type list")
        for flag in flags:
            if not isinstance(flag, unicode):
                raise EmailException(u"Email.__init__: flags element must be of type unicode")
        self.flags = flags

        if not isinstance(subject, unicode):
            raise EmailException(u"Email.__init__: subject must be of type unicode")
        self.subject = subject

        if not isinstance(body, (str, bytes, types.NoneType)):
            raise EmailException(u"Email.__init__: body must be of type str/bytes")
        self.body = body

        if not isinstance(body_ref_id, (unicode, types.NoneType)):
            raise EmailException(u"Email.__init__: body_ref_id must be of type unicode")
        self.body_ref_id = body_ref_id

        if not isinstance(attachments, list):
            raise EmailException(u"Email.__init__: attachments must be of type list")
        for attachment in attachments:
            if not isinstance(attachment, Attachment):
                raise EmailException(u"Email.__init__: bad attachment")
        self.attachments = attachments

        if not isinstance(in_reply_to, (unicode, types.NoneType)):
             raise EmailException(u"Email.__init__: in_reply_to must be of type unicode")
        self.in_reply_to = in_reply_to

        if not isinstance(references, list):
            raise EmailException(u"Email.__init__: references must be of type list")
        refs= []
        for reference in references:
            if not isinstance(reference, unicode):
                # bad reference is fine, threading algo should work for the most part
                continue
            refs.append(reference)
        self.references = refs

        if not isinstance(message_id, unicode):
            raise EmailException(u"Email.__init__: message_id must be of type unicode")
        self.message_id = message_id

        # below are the fields that new sending emails won't have
        if not isinstance(server_id, (unicode, types.NoneType)):
            raise EmailException(u"Email.__init__: server_id must be of type unicode")
        self.server_id = server_id

        if not isinstance(revision_id, (int, types.NoneType)):
            raise EmailException(u"Email.__init__: revision_id must be of type int")
        self.revision_id = revision_id

        if not isinstance(protocol_version, (int)):
            raise EmailException(u"Email.__init__: protocol_version must be of type int")
        self.protocol_version = protocol_version

        if not isinstance(mailbox_server_id, (unicode, types.NoneType)):
            raise EmailException(u"Email.__init__: mailbox_server_id must be of type unicode")
        self.mailbox_server_id = mailbox_server_id

        if not isinstance(mailbox_name, (unicode, types.NoneType)):
            raise EmailException(u"Email.__init__: mailbox_name must be of type unicode")
        self.mailbox_name = mailbox_name

        if not isinstance(version, (unicode, types.NoneType)):
            raise EmailException(u"Email.__init__: version must be of type unicode")
        self.version = version

        if not isinstance(uid, (int, types.NoneType)):
            raise EmailException(u"Email.__init__: uid must be of type int")
        self.uid = uid

        if not isinstance(thread_id, (unicode, types.NoneType)):
            raise EmailException(u"Email.__init__: thread_id must be of type unicode")
        self.thread_id = thread_id

        if not isinstance(snippet, unicode):
            raise EmailException(u"Email.__init__: snippet must be of type unicode")
        self.snippet = snippet

        if not isinstance(server_time, (int, types.NoneType)):
            raise EmailException(u"Email.__init__: server_time must be of type int")
        self.server_time = server_time

        if not isinstance(expunged, (bool, types.NoneType)):
            raise EmailException(u"Email.__init__: expunged must be of type bool")
        self.expunged = expunged

    def __deepcopy__(self, memo):
        return Email.fromDict(copy.deepcopy(self.toDict()))

    def toMIME(self):
        if self.body == None or ( len(self.attachments) > 0 and any([attachment.content == None for attachment in self.attachments])):
            raise EmailException(u"toMIME: All content must be loaded!")

        if self.protocol_version == PROTOCOL_VERSION.V1:
            try:
                status, message = _restoreAttachments(mime.create.from_string(self.body), {libnacl.encode.hex_encode(libnacl.crypto_hash(att.content)): mime.create.from_string(att.content) for att in self.attachments})
                if status == False:
                    raise EmailException(u"toMIME: failed to restore atts")
                # Reporting the server reception time,
                # 1) similar to what we report to browser,
                # 2) Dates added by MUAs can be incorrect
                if self.server_time:
                    date = (u"%s" + u"\r\n") % email.utils.formatdate(self.server_time)
                    message.headers["Date"] = date

            except mime.MimeError as e:
                raise EmailException(u"toMIME: flanker exception {}".format(e))

        elif self.protocol_version == PROTOCOL_VERSION.V2:
            status, body = Email.deserializeBody(self.body)
            if status == False:
                raise EmailException(u"toMIME: Failed to deserialize body")

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
                if self.server_time:
                    date = (u"%s" + u"\r\n") % email.utils.formatdate(self.server_time)
                    message.headers["Date"] = date

            except mime.EncodingError as e:
                raise EmailException(u"toMIME: exception, {}".format(e))

        else:
            raise EmailException(u"toMIME: protocol_version not supported")

        return message

    @staticmethod
    def serializeBody(body):
        if not isinstance(body, dict):
            return False, None
        return Email.encodeContentIfUnicode(misc.jdumps({"text": body.get("text"), "html": body.get("html")}))

    @staticmethod
    def deserializeBody(body):
        if not isinstance(body, (str, bytes)):
            return False, None
        status, body = misc.utf8Decode(body)
        if status == False:
            return False, None
        return misc.jloads(body)

    def loadBody(self, content):
        self.body = content

    def toDict(self):
        return {
            "revision_id": self.revision_id,
            "version": self.version,
            "snippet": self.snippet,
            "uid": self.uid,
            "thread_id": self.thread_id,
            "mailbox_server_id": self.mailbox_server_id,
            "mailbox_name": self.mailbox_name,
            "flags": self.flags,
            "message_id": self.message_id,
            "server_time": self.server_time,
            "subject": self.subject,
            "sender": self.sender,
            "tos": self.tos,
            "ccs": self.ccs,
            "bccs" : self.bccs,
            "in_reply_to" : self.in_reply_to,
            "reply_to": self.reply_to,
            "references" : self.references,
            "attachments" : [attachment.toDict() for attachment in self.attachments],
            "body": self.body,
            "body_ref_id": self.body_ref_id,
            "expunged": self.expunged,
            "protocol_version": self.protocol_version
        }

    # toBrowser is only to conform with browser expectations and can be removed
    def toBrowser(self, with_body=False):
        o = {}
        o["unique_id"] = self.server_id
        o["snippet"] = self.snippet
        o["uid"] = self.uid
        o["thread_id"] = self.thread_id
        o["mailbox_name"] = self.mailbox_name
        o["mailbox_id"] = self.mailbox_server_id
        o["flags"] = self.flags
        o["message_id"] = self.message_id
        o["date"] = email.utils.formatdate(self.server_time)
        o["subject"] = self.subject
        o["sender"] = {"address": self.sender["user_id"], "name": self.sender["display_name"]}
        o["tos"] = [{"address": to["user_id"], "name": to["display_name"]} for to in self.tos]
        o["ccs"] = [{"address": cc["user_id"], "name": cc["display_name"]} for cc in self.ccs]
        o["bccs"] = [{"address": bcc["user_id"], "name": bcc["display_name"]} for bcc in self.bccs]
        o["in_reply_to"] = self.in_reply_to
        o["references"] = self.references

        if with_body:
            if self.protocol_version == PROTOCOL_VERSION.V1:
                try:
                    message = self.toMIME()
                    text, html, attachments = _parseMIME(message)
                    status, body = Email.serializeBody({"text": text, "html": html})
                    if status == False:
                        raise EmailException(u"toBrowser: failed to serialize body")

                except mime.MimeError as e:
                    raise EmailException(u"toBrowser: exception {}".format(e))

            elif self.protocol_version == PROTOCOL_VERSION.V2:
                body = self.body
                attachments = self.attachments

            else:
                raise EmailException(u"toBrowser: protocol_version not supported")

            if body == None:
                body = {"text": u"", "html": u""}
            else:
                status, body = Email.deserializeBody(body)
                if status == False:
                    raise EmailException(u"toBrowser: Failed to deserialize body")

            browser_atts = []
            for att in attachments:
                status, encoded = misc.b64enc(att.content)
                if status == False:
                    continue

                browser_atts.append({
                    "filename": att.metadata.filename,
                    "content_type": att.metadata.content_type,
                    "size": len(att.content),
                    "content_disposition": att.metadata.content_disposition,
                    "content": encoded,
                    "content_id": att.metadata.content_id
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

# V2 to V1 conversion is a pure function. While V1 to V2 conversion is not pure because of the alternating boundaries
def V2ToV1(email):
    if not isinstance(email, Email) or email.protocol_version != PROTOCOL_VERSION.V2:
        raise EmailException(u"V2ToV1: COnvertor invalid input")

    message = email.toMIME()
    return Email.fromMIME(message, email.server_id, email.revision_id, \
                            PROTOCOL_VERSION.V1, email.version, email.snippet, email.uid, \
                            email.thread_id, email.mailbox_server_id, email.flags, \
                            email.message_id, email.server_time, email.subject, \
                            email.sender, email.tos, email.ccs, email.bccs, email.reply_to, email.in_reply_to, email.references, email.expunged)

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

def _separateAttachments(msg):
    msg = mime.create.from_string(msg.to_string())
    if msg.content_type.is_multipart():
        # An email is a tree consisting of interior nodes, which have
        # Content-Type: multipart/*, and leaf nodes (bodies, attachments)
        new_parts = []
        attachments = []
        for p in msg.parts:
            new_p, atts = _separateAttachments(p)
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
        att_hash = libnacl.encode.hex_encode(libnacl.crypto_hash(msg.to_string()))
        # Insert a dummy node into the message tree so we know where to insert
        # this attachment when reconstructing the email
        placeholder = mime.create.attachment(DUMMY_CONTENT_TYPE, u"placeholder for an attachment", filename=att_hash, disposition=DUMMY_DISPOSITION)
        return placeholder, [msg]

def _restoreAttachments(msg, atts):
    if msg.content_type.is_multipart():
        new_parts = []
        for x in msg.parts:
            status, new_part = _restoreAttachments(x, atts)
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

# Using this with the flanker MIME class forces it to always reparse the
# entire object before outputting it in the to_string() method.  This is
# useful when we modify the objects internals thru an unsanctioned interface.
def was_changed_always(self, ignore_prepends=False):
    return True

def _parseMIME(raw_mime):
    text = None
    html = None
    attachments = []
    for part in raw_mime.walk(with_self=True, skip_enclosed=True):
        if part.content_type.is_multipart():
            continue
        t, o = part.content_disposition
        filename = o.get("filename")
        if filename == None:
            filename = u"untitled"

        if part.content_type.is_message_container():
            part_content = part.enclosed.to_string()
        else:
            part_content = part.body

        if t == u"attachment":
            status, encoded = Email.encodeContentIfUnicode(part_content)
            if status == False:
                raise EmailException(u"parseMIME: failed to utf-8 encode a unicode attachment")
            attachments.append({
                "metadata": {
                    "filename": filename,
                    "content_type": u"{}/{}".format(part.content_type.main,part.content_type.sub),
                    "content_disposition": u"attachment"
                },
                "content": encoded
            })

        elif t == u"inline" or t is None: # presentation is inline
            if part.content_type.value == u"text/plain":
                if text is None:
                    text = part_content
                else:
                    text = text + u"\n" + part_content
            elif part.content_type.value == u"text/html":
                if html is None:
                    html = part_content
                else:
                    html = html + u"<br>" + part_content
            elif t == u"inline":
                content_id = part.headers.get("Content-Id", None)
                # Part with inline disposition preference and no content-id should be
                # displayed where the part is located in the MIME per RFC
                if content_id is None:
                    cid = Email.newMessageId()
                    # TODO: add when inline presentation ready on front end
                    # if part.content_type.main == u"image":
                    #     if html is None:
                    #         html = u"<img src=\"cid:{}\">".format(cid)
                    #     else:
                    #         html = html + u"<br>" + u"<img src=\"cid:{}\">".format(cid)
                    # else:
                    #     if html is None:
                    #         html = u"<object data=\"cid:{}\" type=\"{}\"></object>".format(cid, part.content_type.value)
                    #     else:
                    #         html = html + u"<br>" + u"<object data=\"cid:{}\" type=\"{}\"></object>".format(cid, part.content_type.value)

                    content_id = u"<{}>".format(cid)
                else:
                     # the content should already have a placeholder in the HTML
                     # if it doesn't, it should show up as a normal attachments when being displayed
                    pass

                status, encoded = Email.encodeContentIfUnicode(part_content)
                if status == False:
                    raise EmailException(u"parseMIME: failed to utf-8 encode a unicode attachment")
                attachments.append({
                    "metadata": {
                        "filename": filename,
                        "content_type": u"{}/{}".format(part.content_type.main,part.content_type.sub),
                        "content_disposition": u"inline",
                        "content_id": content_id
                    },
                    "content": encoded
                })
            else:
                # this part has no info on it's presentation and is not text or html, hence, should default to attachment
                status, encoded = Email.encodeContentIfUnicode(part_content)
                if status == False:
                    raise EmailException(u"parseMIME: failed to utf-8 encode a unicode attachment")

                attachments.append({
                    "metadata": {
                        "filename": filename,
                        "content_type": u"{}/{}".format(part.content_type.main,part.content_type.sub),
                        "content_disposition": u"attachment"
                    },
                    "content": encoded
                })
        else: # Unknown content_dispositions, wrapping it as an attachment per RFC 2183
            status, encoded = Email.encodeContentIfUnicode(part_content)
            if status == False:
                raise EmailException(u"parseMIME: failed to utf-8 encode a unicode attachment")
            attachments.append({
                "metadata": {
                    "filename": filename,
                    "content_type": part.content_type.value,
                    "content_disposition": u"attachment"
                },
                "content": encoded
            })

    attachments = [Attachment.fromDict(attachment) for attachment in attachments]
    return text, html, attachments

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
