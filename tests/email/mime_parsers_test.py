# vim: set fileencoding=utf-8 :
import StringIO, time, email.utils, re
from pvHelpers import randUnicode, Attachment, AttachmentMetadata, randStr, createMime, parseMime, AttachmentType, EmailException, EmailHelpers
from werkzeug.datastructures import FileStorage
from flanker import addresslib, mime
import pytest


def test_create_plain_mime():
    # html/text can't be None
    with pytest.raises(EmailException) as e:
        createMime(None, u"html", [])
    with pytest.raises(EmailException) as e:
        createMime(u"text", None, [])

    text = randUnicode(length=1024)
    html = randUnicode(length=1024)
    raw_mime = createMime(text, html, [])
    assert raw_mime.content_type.value == u"multipart/alternative"

    assert len(raw_mime.parts) == 1 + 1
    assert set(["(text/html)", "(text/plain)"]) == set(map(lambda p: str(p), raw_mime.parts))
    assert text == filter(lambda p:str(p) == "(text/plain)", raw_mime.parts)[0].body
    assert html == filter(lambda p:str(p) == "(text/html)", raw_mime.parts)[0].body

    # test that quotable encoding always has the correct softline break as "=\r\n"
    assert len(re.findall("=\n", raw_mime.to_string())) == 0


def test_create_mime_with_regular_attachment():
    text = randUnicode(length=1024)
    html = randUnicode(length=1024)
    attachments = []
    for _ in range(4):
        content = randStr(size=4096)
        _filename = randUnicode()
        f = FileStorage(stream=StringIO.StringIO(content), filename=_filename, content_type="image/jpeg")
        attachments.append(Attachment.fromFileStorage(f, AttachmentMetadata(f.filename, f.content_type)))

    raw_mime = createMime(text, html, attachments)
    assert raw_mime.content_type.value == u"multipart/mixed"
    # 1 part is for text/html content, and one for each attachment
    assert len(raw_mime.parts) == len(attachments) + 1
    body_parts = filter(lambda p: p.content_type.value == u"multipart/alternative", raw_mime.parts)
    assert len(body_parts) == 1
    body_part = body_parts[0]
    assert set(["(text/html)", "(text/plain)"]) == set(map(lambda p: str(p), body_part.parts))
    attachment_parts = filter(lambda p: p.content_disposition[0] == AttachmentType.ATTACHMENT, raw_mime.parts)
    assert set(map(lambda att: att.metadata.content_disposition, attachments)) == set(map(lambda att_part: att_part.content_disposition[0], attachment_parts))
    assert set(map(lambda att: att.metadata.filename, attachments)) == set(map(lambda att_part: att_part.content_disposition[1]["filename"], attachment_parts))
    assert set(map(lambda att: att.content.content, attachments)) == set(map(lambda att_part: att_part.body, attachment_parts))
    assert len(re.findall("=\n", raw_mime.to_string())) == 0


def test_create_mime_with_inline_attachment():
    text = randUnicode(length=1024)
    html = randUnicode(length=1024)
    attachments = []
    for _ in range(4):
        content = randStr(size=4096)
        _filename = randUnicode()
        f = FileStorage(stream=StringIO.StringIO(content), filename=_filename, content_type="image/jpeg")
        att = Attachment.fromFileStorage(f, AttachmentMetadata(f.filename, f.content_type))
        att.metadata.content_disposition = AttachmentType.INLINE
        attachments.append(att)


    raw_mime = createMime(text, html, attachments)
    assert raw_mime.content_type.value == u"multipart/alternative"
    # 1 part is for text/plain content, and one for multipart/related
    assert set(["(multipart/related)", "(text/plain)"]) == set(map(lambda p: str(p), raw_mime.parts))
    assert text == filter(lambda p:str(p) == "(text/plain)", raw_mime.parts)[0].body
    related_part = filter(lambda p: str(p) == "(multipart/related)", raw_mime.parts)[0]
    # one for html and rest inline atts
    assert len(related_part.parts) == len(attachments) + 1
    assert html == filter(lambda p:str(p) == "(text/html)", related_part.parts)[0].body
    attachment_parts = filter(lambda p: p.content_disposition[0] == AttachmentType.INLINE, related_part.parts)
    assert set(map(lambda att: att.metadata.filename, attachments)) == set(map(lambda att_part: att_part.content_disposition[1]["filename"], attachment_parts))
    assert set(map(lambda att: att.content.content, attachments)) == set(map(lambda att_part: att_part.body, attachment_parts))
    assert len(re.findall("=\n", raw_mime.to_string())) == 0


def test_create_mime_with_inline_and_regular_attachment():
    text = randUnicode(length=1024)
    html = randUnicode(length=2048)
    attachments = []
    for _ in range(4):
        content = randStr(size=4096)
        _filename = randUnicode()
        f = FileStorage(stream=StringIO.StringIO(content), filename=_filename, content_type="image/jpeg")
        att = Attachment.fromFileStorage(f, AttachmentMetadata(f.filename, f.content_type))
        att.metadata.content_disposition = AttachmentType.INLINE
        attachments.append(att)

    for _ in range(4):
        content = randStr(size=1024)
        _filename = randUnicode()
        f = FileStorage(stream=StringIO.StringIO(content), filename=_filename, content_type="image/jpeg")
        attachments.append(Attachment.fromFileStorage(f, AttachmentMetadata(f.filename, f.content_type)))

    raw_mime = createMime(text, html, attachments)
    assert raw_mime.content_type.value == u"multipart/mixed"
    # 1 part should be for multipart/alternative , and one for each regular attachment
    assert len(raw_mime.parts) == len(filter(lambda att: att.metadata.content_disposition == AttachmentType.ATTACHMENT, attachments)) + 1
    assert "(multipart/alternative)" in map(lambda p: str(p), raw_mime.parts)
    # testing regular atts content
    assert set(map(lambda att: att.content.content, filter(lambda att: att.metadata.content_disposition == AttachmentType.ATTACHMENT, attachments))) == set(map(lambda att_part: att_part.body, filter(lambda p: p.content_disposition[0] == AttachmentType.ATTACHMENT, raw_mime.parts)))

    # test alternate_part
    alternate_part = filter(lambda p: p.content_type.value == "multipart/alternative", raw_mime.parts)[0]
    assert set(["(multipart/related)", "(text/plain)"]) == set(map(lambda p: str(p), alternate_part.parts))
    assert text == filter(lambda p:str(p) == "(text/plain)", alternate_part.parts)[0].body
    related_part = filter(lambda p: str(p) == "(multipart/related)", alternate_part.parts)[0]

    # one for html and rest inline atts
    assert len(related_part.parts) == len(filter(lambda att: att.metadata.content_disposition == AttachmentType.INLINE, attachments)) + 1
    assert html == filter(lambda p:str(p) == "(text/html)", related_part.parts)[0].body
    inline_attachment_parts = filter(lambda p: p.content_disposition[0] == AttachmentType.INLINE, related_part.parts)
    assert set(map(lambda att: att.metadata.filename, filter(lambda att: att.metadata.content_disposition == AttachmentType.INLINE, attachments))) == set(map(lambda att_part: att_part.content_disposition[1]["filename"], inline_attachment_parts))
    assert set(map(lambda att: att.content.content, filter(lambda att: att.metadata.content_disposition == AttachmentType.INLINE, attachments))) == set(map(lambda att_part: att_part.body, inline_attachment_parts))
    assert len(re.findall("=\n", raw_mime.to_string())) == 0


def test_create_mime_headers_validity():
    text = randUnicode(length=2012)
    html = randUnicode(length=2014)
    attachments = []
    for _ in range(4):
        content = randStr(size=2017)
        _filename = randUnicode()
        f = FileStorage(stream=StringIO.StringIO(content), filename=_filename, content_type="image/jpeg")
        attachments.append(Attachment.fromFileStorage(f, AttachmentMetadata(f.filename, f.content_type)))

    message_id = randUnicode()
    _time = time.time()
    tos = [{"user_id": randUnicode()+"@x.com", "display_name": randUnicode()} for _ in range(12)]
    ccs = [{"user_id": randUnicode()+"@x.com", "display_name": randUnicode()} for _ in range(4)]
    bccs = [{"user_id": randUnicode()+"@x.com", "display_name": randUnicode()} for _ in range(3)]
    references = [randUnicode() for _ in range(5)]
    in_reply_to = randUnicode()
    subject = randUnicode()
    reply_tos = [{"user_id": randUnicode()+"@x.com", "display_name": randUnicode()} for _ in range(2)]
    sender = {"user_id": randUnicode()+"@x.com", "display_name": randUnicode()}
    raw_mime = createMime(text, html, attachments, message_id, _time, subject, tos, ccs, bccs, reply_tos, sender, in_reply_to, references)
    assert message_id == raw_mime.headers.get("Message-Id")
    assert tos == [{"user_id": to.address, "display_name": to.display_name} for to in addresslib.address.parse_list(raw_mime.headers.get("To"))]
    assert ccs == [{"user_id": cc.address, "display_name": cc.display_name} for cc in addresslib.address.parse_list(raw_mime.headers.get("Cc"))]
    assert bccs == [{"user_id": bcc.address, "display_name": bcc.display_name} for bcc in addresslib.address.parse_list(raw_mime.headers.get("Bcc"))]
    assert reply_tos == [{"user_id": rpt.address, "display_name": rpt.display_name} for rpt in addresslib.address.parse_list(raw_mime.headers.get("Reply-To"))]
    assert "{} <{}>".format(sender["display_name"], sender["user_id"]) == raw_mime.headers.get("From")
    assert subject == raw_mime.headers.get("Subject")
    assert references == raw_mime.headers.get("references").split(" ")
    assert in_reply_to == raw_mime.headers.get("in-reply-to")
    assert email.utils.formatdate(_time) == raw_mime.headers.get("Date")
    assert len(re.findall("=\n", raw_mime.to_string())) == 0


def test_parse_mime_only_plaintext():
    raw_mime = mime.create.text("plain", randUnicode(length=32321))

    text, html, attachments = parseMime(raw_mime)

    assert text == raw_mime.body
    # if not alternative, text should be wrapped inside html
    assert html == u"<div data-preveil-text>{}</div>".format(raw_mime.body)
    assert attachments == []


def test_parse_mime_text_html():
    raw_mime = mime.create.text("html", randUnicode(length=2))
    text, html, attachments = parseMime(raw_mime)

    assert text == u""
    assert html == raw_mime.body
    assert attachments == []


def test_parse_mime_nested_alternative_and_text():
    root_mime = mime.create.multipart("mixed")
    text_1 = mime.create.text("plain", randUnicode(length=1))
    root_mime.append(text_1)

    alternate_mime = mime.create.multipart("alternative")
    text_2 = mime.create.text("plain", randUnicode(length=2))
    html_2 = mime.create.text("html", randUnicode(length=3))
    alternate_mime.append(text_2)
    alternate_mime.append(html_2)
    root_mime.append(alternate_mime)
    text_3 = mime.create.text("plain", randUnicode(length=5))
    root_mime.append(text_3)

    text, html, attachments = parseMime(root_mime)

    assert text == u"\n".join([text_1.body, text_2.body, text_3.body])
    # non alternate text gets added to html
    assert html == u"<br>".join([u"<div data-preveil-text>{}</div>".format(text_1.body), html_2.body, u"<div data-preveil-text>{}</div>".format(text_3.body)])
    assert attachments == []


def test_parse_mime_regular_attachment():
    root_mime = mime.create.multipart("mixed")
    text_1 = mime.create.text("plain", randUnicode(length=1))
    root_mime.append(text_1)

    for _ in range(3):
        att = mime.create.attachment(u"image/png", randStr(size=12355), randUnicode(), AttachmentType.ATTACHMENT)
        root_mime.append(att)

    text, html, attachments = parseMime(root_mime)

    assert text == text_1.body
    # non alternate text gets added to html
    assert html == u"<br>".join([u"<div data-preveil-text>{}</div>".format(text_1.body)])
    # all are regular atts
    assert all(map(lambda att: att.metadata.content_disposition == AttachmentType.ATTACHMENT, attachments))
    # all the atts exist w right content
    assert map(lambda att: att.content.content, attachments) == map(lambda att_part: att_part.body, filter(lambda p: p.content_disposition[0] == AttachmentType.ATTACHMENT, root_mime.parts))

    #add some nested atts
    nested_mime = mime.create.multipart("mixed")
    html_1 = mime.create.text("html", randUnicode(length=454))
    nested_mime.append(html_1)
    for _ in range(5):
        att = mime.create.attachment(u"application/octet-stream", randStr(size=545), randUnicode(length=12), AttachmentType.ATTACHMENT)
        nested_mime.append(att)

    root_mime.append(nested_mime)

    text, html, attachments = parseMime(root_mime)
    assert text == text_1.body
    # non alternate text gets added to html
    assert html == u"<br>".join([u"<div data-preveil-text>{}</div>".format(text_1.body), html_1.body])
    # all are regular atts
    assert all(map(lambda att: att.metadata.content_disposition == AttachmentType.ATTACHMENT, attachments))
    # all the atts exist w right content
    assert map(lambda att: att.content.content, attachments) == map(lambda att_part: att_part.body, filter(lambda p: p.content_disposition[0] == AttachmentType.ATTACHMENT, root_mime.parts + nested_mime.parts))


def test_parse_mime_inline_attachment():
    root_mime = mime.create.multipart("related")
    html_1 = mime.create.text("html", randUnicode(length=10))
    root_mime.append(html_1)

    for _ in range(6):
        att = mime.create.attachment(u"image/png", randStr(size=235), randUnicode(), AttachmentType.INLINE)
        root_mime.append(att)

    text, html, attachments = parseMime(root_mime)

    assert text == u""
    #the 3 attachments should be inline and have content id assigned to them
    assert len(attachments) == 6
    assert all([att.metadata.content_disposition == AttachmentType.INLINE for att in attachments])
    matches = re.findall("<div data-preveil-inline>(.*?)</div>", html, flags=re.DOTALL)
    # all are inline
    assert len(matches) == len(attachments)
    # make sure all the content ids are included
    content_ids = [re.findall('src="(.*?)"',img)[0] for img in matches]
    content_ids = [re.subn("cid:", "<", ci)[0] + ">" for ci in content_ids]
    assert content_ids == [att.metadata.content_id for att in attachments]

    # test when inline atts have content_id
    root_mime = mime.create.multipart("alternative")
    text_1 = mime.create.text("plain", randUnicode(length=19))
    root_mime.append(text_1)
    related_mime = mime.create.multipart("related")
    html_1 = mime.create.text("html", randUnicode(length=15))
    related_mime.append(html_1)
    att = mime.create.attachment(u"application/octet-stream", randStr(size=421), randUnicode(), AttachmentType.INLINE)
    cid = EmailHelpers.newMessageId()
    att.headers["Content-Id"] = cid
    related_mime.append(att)
    root_mime.append(related_mime)
    text, html, attachments = parseMime(root_mime)
    assert len(attachments) == 1
    assert cid == attachments[0].metadata.content_id
    assert len(re.findall("data-preveil-inline", html)) == 0


def test_invalid_content_disposition():
    root_mime = mime.create.multipart("mixed")
    text_1 = mime.create.text("plain", randUnicode(length=1653))
    root_mime.append(text_1)

    att = mime.create.attachment(u"image/png", randStr(size=2052), randUnicode(), u"invalidCD")
    root_mime.append(att)

    text, html, attachments = parseMime(root_mime)

    assert text == text_1.body
    # non alternate text gets added to html
    assert html == u"<br>".join([u"<div data-preveil-text>{}</div>".format(text_1.body)])
    assert len(attachments) == 1
    # assert that the bad CD has translated as a regular attachment
    assert attachments[0].metadata.content_disposition == AttachmentType.ATTACHMENT
    # all attachment still has the right content
    assert attachments[0].content.content == filter(lambda p: p.content_disposition[0] == u"invalidCD", root_mime.parts)[0].body


def test_unknown_content_type_with_no_disposition():
    root_mime = mime.create.multipart("mixed")
    text_1 = mime.create.text("plain", randUnicode(length=1332))
    root_mime.append(text_1)

    att = mime.create.attachment(u"image/png", randStr(size=8722), randUnicode(), AttachmentType.ATTACHMENT)
    root_mime.append(att)

    content = randUnicode(length=1523)
    unknown_part = mime.create.text("plain", content)
    unknown_part.headers["Content-Type"] = mime.message.ContentType(u"xx", u"yy")

    root_mime.append(unknown_part)

    text, html, attachments = parseMime(root_mime)

    assert text == text_1.body
    # non alternate text gets added to html
    assert html == u"<br>".join([u"<div data-preveil-text>{}</div>".format(text_1.body)])
    assert len(attachments) == 2
    # assert that the bad content type has translated in as a regular attachment
    assert map(lambda att: att.metadata.content_disposition, attachments) == [AttachmentType.ATTACHMENT]*2
    # all attachment still has the right content
    assert map(lambda att: att.content.content, attachments) == map(lambda p: p.body, filter(lambda p: p.content_type.value != u"text/plain", root_mime.parts))
