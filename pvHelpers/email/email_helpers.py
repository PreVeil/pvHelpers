from ..misc import utf8Encode, jdumps, jloads, utf8Decode
import uuid

DUMMY_DISPOSITION = u"dummy"
DUMMY_CONTENT_TYPE = u"dummy/dummy"
MAILBOX_ALIAS = {u"INBOX":u"inbox", u"Drafts":u"drafts", u"Sent Messages":u"sent", u"Deleted Messages":u"trash"}

class PROTOCOL_VERSION():
    V1 = 1
    V2 = 2
    V3 = 3
    V4 = 4

class EmailException(Exception):
    def __init__(self, message=u""):
        Exception.__init__(self, message)

#########################################
######### Factory Common Mixins #########
#########################################
class EmailHelpers(object):
    ###FIXME: this works when we only have aliases for the 4 default maiboxes,
    # and use the real "DB" mailbox_name for a custom mailbox
    @staticmethod
    def getMailboxAlias(mailbox_name):
        if mailbox_name in MAILBOX_ALIAS:
            return MAILBOX_ALIAS[mailbox_name]
        return mailbox_name

    @staticmethod
    def newMessageId():
        return u"{}@preveil.com".format(str(uuid.uuid4()))

    @staticmethod
    def encodeContentIfUnicode(content):
        if isinstance(content, unicode):
            return utf8Encode(content)
        return True, content

    @staticmethod
    def serializeBody(body):
        if not isinstance(body, dict):
            return False, None
        return EmailHelpers.encodeContentIfUnicode(jdumps({"text": body.get("text"), "html": body.get("html")}))

    @staticmethod
    def deserializeBody(body):
        if not isinstance(body, (str, bytes)):
            return False, None
        status, body = utf8Decode(body)
        if status == False:
            return False, None
        return jloads(body)

    @staticmethod
    def parseMIME(raw_mime):
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
