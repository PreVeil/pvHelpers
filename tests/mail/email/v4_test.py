# vim: set fileencoding=utf-8 :
import os
import StringIO

from pvHelpers.mail import EmailFactory
from pvHelpers.mail.email import (Attachment, AttachmentMetadata,
                                  AttachmentType, Content, EmailHelpers, PROTOCOL_VERSION)
from pvHelpers.utils import NOT_ASSIGNED, randUnicode
from werkzeug.datastructures import FileStorage


class User():
    def __init__(self):
        self.user_id = randUnicode()
        self.display_name = randUnicode()


def create_email_v4(sender, tos, ccs, bccs, subject, text, html, attachments,
                    in_reply_to, references, reply_tos=[], flags=[],
                    server_attr=NOT_ASSIGNED(), message_id=None):
    if message_id is None:
        message_id = u"<{}>".format(EmailHelpers.new_message_id())
    body = EmailHelpers.serialize_body({"text": text, "html": html})
    return EmailFactory.new(**{
        "server_attr": server_attr,
        "flags": flags,
        "subject": subject,
        "sender": {"user_id": sender.user_id, "display_name": sender.display_name},
        "tos": [{"user_id": to.user_id, "display_name": to.display_name} for to in tos],
        "ccs": [{"user_id": cc.user_id, "display_name": cc.display_name} for cc in ccs],
        "bccs": [{"user_id": bcc.user_id, "display_name": bcc.display_name} for bcc in bccs],
        "message_id": message_id,
        "body": Content(body),
        "attachments": [Attachment.from_file_storage(
            _file, AttachmentMetadata(_file.filename, _file.content_type)) for _file in attachments],
        "in_reply_to": in_reply_to,
        "reply_tos": [],
        "references": references,
        "protocol_version": PROTOCOL_VERSION.V4
    })


def test_to_mime():
    from_account, to_account = User(), User()
    # with no attachments
    attachments = []
    email = create_email_v4(
        from_account, [to_account], [], [], u"S S", u"text", u"html", attachments, None, [], [], [])
    raw_mime = email.to_mime()

    assert raw_mime.content_type.is_multipart()
    parts = []
    for part in raw_mime.walk(with_self=True):
        parts.append(part)

    assert parts[0].content_type == "multipart/alternative"
    assert parts[1].content_type == "text/plain"
    assert parts[1].body == "text"
    assert parts[2].content_type == "text/html"
    assert parts[2].body == "html"

    # with multiple atts
    attachments = [
        FileStorage(
            stream=StringIO.StringIO(os.urandom(1024)), filename=randUnicode(), content_type="image/png"),
        FileStorage(
            stream=StringIO.StringIO(os.urandom(1024)), filename=randUnicode(), content_type="video/mp4"),
        FileStorage(
            stream=StringIO.StringIO(os.urandom(1024)),
            filename=randUnicode(), content_type="application/octet-stream"),
        FileStorage(stream=StringIO.StringIO(randUnicode()), filename=randUnicode(), content_type="text/html"),
    ]
    email = create_email_v4(from_account, [to_account], [], [], u"subject", u"a", u"b", attachments, None, [])
    raw_mime = email.to_mime()

    assert raw_mime.content_type.is_multipart()
    parts = []
    for part in raw_mime.walk(with_self=True):
        parts.append(part)

    assert parts[0].content_type == "multipart/mixed"
    assert parts[1].content_type == "multipart/alternative"
    assert parts[2].content_type == "text/plain"
    assert parts[2].body == "a"
    assert parts[3].content_type == "text/html"
    assert parts[3].body == "b"
    assert parts[4].content_type == "image/png"
    assert parts[5].content_type == "video/mp4"
    assert parts[6].content_type == "application/octet-stream"
    assert parts[7].content_type == "text/html"

    # lets make first attachment inline
    email.attachments[0].metadata.content_disposition = AttachmentType.INLINE
    raw_mime = email.to_mime()
    assert raw_mime.content_type.is_multipart()
    parts = []
    for part in raw_mime.walk(with_self=True):
        parts.append(part)

    assert parts[0].content_type == "multipart/mixed"
    assert parts[1].content_type == "multipart/alternative"
    assert parts[2].content_type == "text/plain"
    assert parts[2].body == "a"
    assert parts[3].content_type == "multipart/related"
    assert parts[4].content_type == "text/html"
    assert parts[4].body == "b"
    assert parts[5].content_type == "image/png"
    assert parts[6].content_type == "video/mp4"
    assert parts[7].content_type == "application/octet-stream"
    assert parts[8].content_type == "text/html"
