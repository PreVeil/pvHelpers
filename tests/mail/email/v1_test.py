# vim: set fileencoding=utf-8 :
import os
import StringIO

from flanker import mime
from pvHelpers.crypto.utils import hex_encode, sha_256_sum
from pvHelpers.mail.email import (Attachment, AttachmentMetadata, AttachmentType,
                                  create_mime, DUMMY_CONTENT_TYPE, EmailHelpers, EmailV1)
from pvHelpers.utils import NotAssigned, rand_str, rand_unicode
from werkzeug.datastructures import FileStorage


class User():
    def __init__(self):
        self.user_id = rand_unicode()
        self.display_name = rand_unicode()


def create_email_v1(sender, tos, ccs, bccs, subject, text, html, attachments,
                    in_reply_to, references, reply_tos=[], flags=[],
                    server_attr=NotAssigned(), message_id=None):
    if message_id is None:
        message_id = u"<{}>".format(EmailHelpers.new_message_id())
    sender = {"user_id": sender.user_id, "display_name": sender.display_name}
    tos = [{"user_id": to.user_id, "display_name": to.display_name} for to in tos]
    ccs = [{"user_id": cc.user_id, "display_name": cc.display_name} for cc in ccs]
    bccs = [{"user_id": bcc.user_id, "display_name": bcc.display_name} for bcc in bccs]
    time = None
    if not isinstance(server_attr, NotAssigned):
        time = server_attr.server_time
    raw_mime = create_mime(
        text, html, [
            Attachment.from_file_storage(_file, AttachmentMetadata(_file.filename, _file.content_type))
            for _file in attachments
        ], message_id, time, subject, tos, ccs, bccs, reply_tos, sender, in_reply_to, references)
    return EmailV1.from_mime(raw_mime.to_string(), flags, sender)


def test_from_mime():
    # create email from separated mime and test if it get reconstructed ok
    root_mime = mime.create.multipart("mixed")
    text_1 = mime.create.text("plain", rand_unicode(length=3))
    root_mime.append(text_1)
    attachments = []
    for _ in range(2):
        a = mime.create.attachment("image/png", rand_str(size=10), rand_unicode(), AttachmentType.INLINE)
        attachments.append(a)
        a.to_string()
        root_mime.append(a)

    text_2 = mime.create.text("plain", rand_unicode(length=3))
    root_mime.append(text_2)
    for _ in range(3):
        a = mime.create.attachment("video/mp4", rand_str(size=15), rand_unicode(), AttachmentType.ATTACHMENT)
        attachments.append(a)
        a.to_string()
        root_mime.append(a)
    root_mime.headers["Message-Id"] = u"<{}>".format(EmailHelpers.new_message_id())
    email = EmailV1.from_mime(root_mime.to_string(), [], {"user_id": u"s@b.com", "display_name": u"S B"})

    # check if the attachments have been all separated properly
    body_mime = mime.from_string(email.body.content)
    assert len(attachments) == len(filter(lambda p: p.content_type.value == DUMMY_CONTENT_TYPE, body_mime.parts))
    # check att hashes are properly inserted as filenames
    assert map(lambda a: hex_encode(sha_256_sum(a.to_string())), attachments) == \
        map(lambda p: p.content_disposition[1]["filename"],
            filter(lambda p: p.content_type.value == DUMMY_CONTENT_TYPE, body_mime.parts))


def test_attachment_reconstruction():
    raw_message = """Received: ConsoleMessageDelivery
From: "(Secure) iOS Dev" <ios@preveil.com>
Content-Type: multipart/related; boundary="Apple-Mail=_B3D4A2AE-CBE5-47E8-86E4-5052190755A6"; type="text/plain"
Subject:
Message-Id: <0A83DC22-971B-418B-BEBF-BA0046C34868@preveil.com>
Date: Mon, 27 Jun 2016 10:43:03 -0400
To: iOS Dev <ios@preveil.com>
Mime-Version: 1.0 (Mac OS X Mail 9.3 (3124))

--Apple-Mail=_B3D4A2AE-CBE5-47E8-86E4-5052190755A6
Content-Transfer-Encoding: 7bit
Content-Type: text/plain;
charset=us-ascii

blah blah blah

--Apple-Mail=_B3D4A2AE-CBE5-47E8-86E4-5052190755A6
Content-Transfer-Encoding: base64
Content-Disposition: dummy; filename="handle"
Content-Type: dummy/dummy; name="handle"

cGxhY2Vob2xkZXIgZm9yIGFuIGF0dGFjaG1lbnQ=
"""
    attachment_content = rand_unicode()
    raw_attachment = \
        "Content-Type: text/plain; name=\"test.txt\"\r\nContent-Disposition: attachment; " + \
        "filename=\"test.txt\"\r\n\r\n{}".format(attachment_content)

    message = mime.from_string(raw_message)
    attachment = mime.from_string(raw_attachment)
    attachments = {"handle": attachment}

    status, restored_message = EmailV1.restore_attachments(message, attachments)
    assert status
    assert len(restored_message.parts) == 2
    assert restored_message.parts[1] == attachment


def test_to_mime():
    from_account, to_account = User(), User()
    # with one attachment
    attachments = [FileStorage(
        stream=StringIO.StringIO(os.urandom(1024)), filename=rand_unicode() + ".jpg", content_type="image/jpeg")]
    email = create_email_v1(
        from_account, [to_account], [], [], u"S S", u"text", u"html", attachments, None, [], [], [])

    raw_mime = email.to_mime()

    assert raw_mime.content_type.is_multipart()
    parts = []
    for part in raw_mime.walk(with_self=True):
        parts.append(part)

    assert parts[0].content_type == "multipart/mixed"
    assert parts[1].content_type == "multipart/alternative"
    assert parts[2].content_type == "text/plain"
    assert parts[2].body == "text"
    assert parts[3].content_type == "text/html"
    assert parts[3].body == "html"
    assert parts[4].content_type == u"image/jpeg"

    # with multiple atts
    attachments = [
        FileStorage(
            stream=StringIO.StringIO(os.urandom(1024)), filename=rand_unicode(), content_type="application/zip"),
        FileStorage(
            stream=StringIO.StringIO(os.urandom(1024)), filename=rand_unicode(), content_type="audio/jpeg"),
        FileStorage(
            stream=StringIO.StringIO(os.urandom(1024)), filename=rand_unicode(), content_type="application/pdf"),
        FileStorage(
            stream=StringIO.StringIO(rand_unicode()), filename=rand_unicode(), content_type="text/plain"),
    ]
    email = create_email_v1(from_account, [to_account], [], [], u"subject", u"a", u"b", attachments, None, [])

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
    assert parts[4].content_type == "application/zip"
    assert parts[5].content_type == "audio/jpeg"
    assert parts[6].content_type == "application/pdf"
    assert parts[7].content_type == "text/plain"
