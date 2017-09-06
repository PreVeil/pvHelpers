from .attachment import Attachment, AttachmentMetadata, AttachmentType
from .content import Content
from .email_helpers import EmailException, EmailHelpers
from ..misc import encodeContentIfUnicode
import email.utils
from flanker import mime, addresslib

def createMime(text, html, attachments, message_id=None, time=None, subject=None, tos=None, ccs=None, bccs=None, reply_tos=None, sender=None, in_reply_to=None, references=None):
    if not isinstance(text, unicode):
        raise EmailException(u"createMime: text must be of type unicode")
    if not isinstance(html, unicode):
        raise EmailException(u"createMime: html must be of type unicode")
    if not isinstance(attachments, list):
        raise EmailException(u"createMime: attachments must be of type list")
    for item in attachments:
        if not isinstance(item, Attachment):
            raise EmailException(u"createMime: attachment must be of type Attachment")

    inline_attachments = filter(lambda att: att.metadata.content_disposition == u"inline" , attachments)
    regular_attachments = filter(lambda att: att.metadata.content_disposition != u"inline" , attachments)
    try:
        #TODO: avoid receiving text from browser, just get html and build the text here
        if html is u"":
            body_shell = mime.create.text("plain", text)
        else:
            if inline_attachments:
                html_part =  mime.create.multipart("related")
                html_part.headers["Content-Type"].params["type"] = u"text/html"
                html_text_part = mime.create.text("html", html)
                html_part.append(html_text_part)
                for att in inline_attachments:
                    html_part.append(att.toMime())
            else:
                html_part = mime.create.text("html", html)

            if text != u"":
                body_shell = mime.create.multipart("alternative")
                body_shell.append(mime.create.text("plain", text), html_part)
            else:
                body_shell = html_part

        if len(regular_attachments) > 0:
            message = mime.create.multipart("mixed")
            message.append(body_shell)
            for att in regular_attachments:
                att_part = att.toMime()
                if att_part.content_type.is_message_container():
                    att_part.headers["Content-Type"].params["name"] = att.metadata.filename
                    att_part.headers["Content-Disposition"].params["filename"] = att.metadata.filename

                message.append(att_part)
        else:
            message = body_shell

        if sender:
            message.headers["From"] = u"{} <{}>".format(sender["display_name"], sender["user_id"])
        if ccs:
            message.headers["Cc"] = u"{}".format(", ".join([u"{} <{}>".format(cc["display_name"], cc["user_id"]) for cc in ccs]))
        if tos:
            message.headers["To"] = u"{}".format(", ".join([u"{} <{}>".format(to["display_name"], to["user_id"]) for to in tos]))
        if bccs:
            message.headers["Bcc"] = u"{}".format(", ".join([u"{} <{}>".format(bcc["display_name"], bcc["user_id"]) for bcc in bccs]))
        if reply_tos:
            message.headers["Reply-To"] = u"{}".format(", ".join([u"{} <{}>".format(rpt["display_name"], rpt["user_id"]) for rpt in reply_tos]))

        if subject:
            message.headers["Subject"] = subject
        if message_id:
            message.headers["Message-Id"] = message_id
        if in_reply_to:
            message.headers["In-Reply-To"] = u"{}".format(in_reply_to)
        if references:
            message.headers["References"] = u"{}".format(" ".join(references))
        if time:
            date = (u"%s" + u"\r\n") % email.utils.formatdate(time)
            message.headers["Date"] = date

    except mime.EncodingError as e:
        raise EmailException(u"createMime: exception, {}".format(e))

    return message

def parseMime(raw_mime):
    if not isinstance(raw_mime, mime.message.part.MimePart):
        raise EmailException(u"parseMime: raw_mime must be of type MimePart")

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

        if t == AttachmentType.ATTACHMENT:
            status, encoded = encodeContentIfUnicode(part_content)
            if status == False:
                raise EmailException(u"parseMime: failed to utf-8 encode a unicode attachment")
            attachments.append(Attachment(AttachmentMetadata(filename, u"{}/{}".format(part.content_type.main, part.content_type.sub), AttachmentType.ATTACHMENT), Content(encoded, None, None)))

        elif t == AttachmentType.INLINE or t is None: # presentation is inline
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
            elif t == AttachmentType.INLINE:
                content_id = part.headers.get("Content-Id", None)
                # Part with inline disposition preference and no content-id should be
                # displayed where the part is located in the MIME per RFC
                if content_id is None:
                    cid = EmailHelpers.newMessageId()
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

                status, encoded = encodeContentIfUnicode(part_content)
                if status == False:
                    raise EmailException(u"parseMime: failed to utf-8 encode a unicode attachment")
                attachments.append(Attachment(AttachmentMetadata(filename, u"{}/{}".format(part.content_type.main, part.content_type.sub), AttachmentType.INLINE, content_id), Content(encoded, None, None)))

            else:
                # this part has no info on it's presentation and is not text or html, hence, should default to attachment
                status, encoded = encodeContentIfUnicode(part_content)
                if status == False:
                    raise EmailException(u"parseMime: failed to utf-8 encode a unicode attachment")
                attachments.append(Attachment(AttachmentMetadata(filename, u"{}/{}".format(part.content_type.main, part.content_type.sub), AttachmentType.ATTACHLINE), Content(encoded, None, None)))

        else: # Unknown content_dispositions, wrapping it as an attachment per RFC 2183
            status, encoded = encodeContentIfUnicode(part_content)
            if status == False:
                raise EmailException(u"parseMime: failed to utf-8 encode a unicode attachment")
            attachments.append(Attachment(AttachmentMetadata(filename, part.content_type.value, AttachmentType.ATTACHLINE), Content(encoded, None, None)))

    return text, html, attachments
