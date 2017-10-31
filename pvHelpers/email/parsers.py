from .attachment import Attachment, AttachmentMetadata, AttachmentType
from .content import Content
from .email_helpers import EmailException, EmailHelpers
from ..misc import encodeContentIfUnicode, g_log
import email.utils
from flanker import mime, addresslib

# Builder creates a simplified mime message that follows the following hierarchy
# https://msdn.microsoft.com/en-us/library/office/aa563064(v=exchg.140).aspx
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
        if inline_attachments:
            html_part =  mime.create.multipart("related")
            html_part.headers["Content-Type"].params["type"] = u"text/html"
            html_text_part = mime.create.text("html", html)
            html_part.append(html_text_part)
            for att in inline_attachments:
                html_part.append(att.toMime())
        else:
            html_part = mime.create.text("html", html)

        body_shell = mime.create.multipart("alternative")

        body_shell.append(
            mime.create.text("plain", text),
            html_part
        )

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

    # wrapping the inserted inline html elements in a distinct element
    def wrapInlineForPV(element_str):
        return u"<div data-preveil-inline>{}</div>".format(element_str)
    def wrapTextForPV(string):
        return u"<div data-preveil-text>{}</div>".format(string.replace("\n", "<br>"))

    text = u""
    html = u""
    attachments = []

    # keeping parent (current_root_c_t, current_root_parts) in a stack while walking
    content_type_stack = []
    # with_self == True so to get singlepart messages processed.
    # skip_enclosed == True so to avoid processing if the message is another message wrapper
    for part in raw_mime.walk(with_self=True, skip_enclosed=True):
        if part.content_type.is_multipart():
            content_type_stack.append((part.content_type.value, list(part.parts)))
            continue

        if len(content_type_stack) > 0:
            try:
                content_type_stack[-1][1].remove(part)
            except ValueError:
                content_type_stack.pop()

        current_root_c_t, current_root_parts = None, []
        if len(content_type_stack) > 0:
            current_root_c_t, current_root_parts = content_type_stack[-1]

        # https://www.ietf.org/rfc/rfc2183.txt has contetn disposition details
        c_d, c_d_other_params = part.content_disposition
        # flanker defaults parts c_t to `ContentType("text", "plain", {'charset': 'ascii'})` if not available
        c_t, c_t_other_params = part.content_type

        filename = c_d_other_params.get("filename") or c_t_other_params.get("name")
        if filename == None:
            filename = u"untitled"

        # `skip_enclosed` is not for inner message containers. i.e. inline `.eml` file.
        # https://github.com/mailgun/flanker/blob/master/flanker/mime/message/part.py#L323-L325
        if part.content_type.is_message_container(): # message/rfc, message/news
            # part.enclosed.body will not have the enclosed message headers
            # we want the entire enclosed message
            part_content = part.enclosed.to_string()
        else:
            part_content = part.body

        content_id = part.headers.get("Content-Id", None)

        if c_d == AttachmentType.ATTACHMENT:
            # python type of the returned body varies
            # depending ONLY on the content_type of the part
            # it'll be `unicode` if content_type is `text/*`
            # this is troublesome for attachment files of `.html` `.txt` `.py`
            # hence should encode them if an attachment
            status, encoded = encodeContentIfUnicode(part_content)
            if status == False:
                raise EmailException(u"parseMime: failed to utf-8 encode a unicode attachment")

            attachments.append(Attachment(AttachmentMetadata(filename, c_t, AttachmentType.ATTACHMENT, content_id), Content(encoded, None, None)))

        elif c_d == AttachmentType.INLINE or c_d is None: # requested presentation of this part is inline
            if c_t == u"text/plain":
                if text is u"":
                    text = part_content
                else:
                    text = text + u"\n" + part_content

                if current_root_c_t != u"multipart/alternative":
                    html_repr = wrapTextForPV(part_content)
                    if html is u"":
                        html = html_repr
                    else:
                        html = html + u"<br>" + html_repr

            elif c_t == u"text/html":
                if html is u"":
                    html = part_content
                else:
                    html = html + u"<br>" + part_content
            # we regard rest of the content_types as attachments
            # more info on multipart/related : https://tools.ietf.org/html/rfc2387
            elif c_d == AttachmentType.INLINE or (current_root_c_t == u"multipart/related" and content_id):
                # Part with inline disposition preference and no content-id should be
                # displayed where the part is located in the MIME per RFC
                # for arbitrary non-displayable types use of icons is suggested/mentioned in rfc
                if content_id is None:
                    # rfc2392 https://tools.ietf.org/html/rfc2392 delves into details of content_id header formating
                    cid = EmailHelpers.newMessageId()
                    content_id = u"<{}>".format(cid)
                    if part.content_type.main == u"image":
                        element = wrapInlineForPV(u"<img src=\"cid:{}\">".format(cid))
                    else:
                        element = wrapInlineForPV(u"<object data=\"cid:{}\" type=\"{}\"></object>".format(cid, c_t))

                    if html is u"":
                        html = element
                    else:
                        html = html + u"<br>" + element

                else:
                     # the content should already have a placeholder in the HTML
                     # if it doesn't, it should show up as a normal attachments when displayed.
                     #
                     # message container parts also fall here message/rfc, message/news
                    pass

                status, encoded = encodeContentIfUnicode(part_content)
                if status == False:
                    raise EmailException(u"parseMime: failed to utf-8 encode a unicode attachment")
                attachments.append(Attachment(AttachmentMetadata(filename, c_t, AttachmentType.INLINE, content_id), Content(encoded, None, None)))

            else:
                # this part has no info on it's presentation and is not text or html, hence, should default to attachment
                status, encoded = encodeContentIfUnicode(part_content)
                if status == False:
                    raise EmailException(u"parseMime: failed to utf-8 encode a unicode attachment")
                attachments.append(Attachment(AttachmentMetadata(filename, c_t, AttachmentType.ATTACHMENT, content_id), Content(encoded, None, None)))

        else: # Unknown content_dispositions, wrapping it as an attachment per RFC 2183
            status, encoded = encodeContentIfUnicode(part_content)
            if status == False:
                raise EmailException(u"parseMime: failed to utf-8 encode a unicode attachment")
            attachments.append(Attachment(AttachmentMetadata(filename, c_t, AttachmentType.ATTACHMENT, content_id), Content(encoded, None, None)))

    return text, html, attachments
