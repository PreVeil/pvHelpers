# vim: set fileencoding=utf-8 :
import copy
import os
import random

from pvHelpers.mail.email import (Attachment, AttachmentMetadata,
                                  AttachmentType, Content, EmailException,
                                  EmailV1)
from pvHelpers.utils import getdir, randStr, randStream, randUnicode
import simplejson
from werkzeug.datastructures import FileStorage

mime_tests = {
  "mime_to_preveil_entity": {
    "description": "These test cases are to verify our parser turning MIME raw source to Preveil Entity.",
    "test_cases": [
      {
        "description": "Image attachments from MacMail",
        "mime": "1.eml",
        "expected_json": "1.json"
      },
      {
        "description": "CSV attachment from MacMail",
        "mime": "2.eml",
        "expected_json": "2.json"
      },
      {
        "description": "HTML, TXT attachments from MacMail",
        "mime": "3.eml",
        "expected_json": "3.json"
      }
    ]
  },
  "preveil_entity_to_mime": {
    "description": "These test cases are to verify our parser turning " +
                   "Preveil Entity to a correct/standard MIME raw source.",
    "test_cases": [{
      "description": "",
      "json": "",
      "expected_mime": ""
    }]
  }
}


def test_attachment_metadata():
    filename = randUnicode()
    content_type = randUnicode()
    content_disposition = randUnicode()
    content_id = randUnicode()
    size = random.randint(0, 1000000000)
    metadata = AttachmentMetadata(filename, content_type, content_disposition, content_id, size)
    assert metadata.to_dict() == {
        "filename": filename,
        "content_type": content_type,
        "content_id": content_id,
        "content_disposition": content_disposition,
        "size": size
    }
    metadata = AttachmentMetadata(filename, None, None, None, None)
    assert metadata.to_dict() == {
        "filename": filename,
        "content_type": u"application/octet-stream",
        "content_id": None,
        "content_disposition": AttachmentType.ATTACHMENT,
        "size": None
    }


def test_attachment_from_file_storage():
    blob = randStream()
    filename = randUnicode()
    content_type = "y/x"
    metadata = AttachmentMetadata(filename, content_type)
    _file = FileStorage(stream=blob, filename=filename, content_type=content_type)
    input_file = copy.deepcopy(_file)
    attachment = Attachment.from_file_storage(input_file, metadata)
    assert attachment.content.content == _file.read()
    assert attachment.metadata.filename == filename
    assert attachment.metadata.content_type == content_type
    assert attachment.metadata.content_disposition == AttachmentType.ATTACHMENT

    # test content_type correction
    blob = randStream()
    filename = randUnicode()
    content_type = "badcontenttype"
    metadata = AttachmentMetadata(filename, content_type)
    _file = FileStorage(stream=blob, filename=filename, content_type=content_type)
    input_file = copy.deepcopy(_file)
    attachment = Attachment.from_file_storage(input_file, metadata)
    assert attachment.content.content == _file.read()
    assert attachment.metadata.filename == filename
    assert attachment.metadata.content_type == "application/octet-stream"
    assert attachment.metadata.content_disposition == AttachmentType.ATTACHMENT


def test_attachment_to_mime():
    filename = randUnicode()
    content_type = "image/png"
    content_disposition = randUnicode()
    content_id = randUnicode()
    metadata = AttachmentMetadata(filename, content_type, content_disposition, content_id)
    blob = randStr(size=1024)

    attachement = Attachment(metadata, Content(blob))
    att_mime = attachement.to_mime()
    assert att_mime.headers.get("Content-Id") == content_id
    assert att_mime.headers.get("Content-Disposition") == (content_disposition, {"filename": filename})
    assert att_mime.headers.get("Content-Type") == content_type
    assert att_mime.body == blob


def test_attachment_from_mime():
    """
    Actions:
        1. parse raw mime sources from mime_tests.py
            Expectation:
            1. Expect the parsed entity to be equivalent to expected results in mime_tests.py
    """
    # Action 1
    test_cases = mime_tests["mime_to_preveil_entity"]["test_cases"]
    for test_case in test_cases:
        with open(os.path.join(getdir(__file__), "test_cases", test_case["mime"]), "r") as f:
            raw_msg = f.read()
        try:
            email = EmailV1.from_mime(raw_msg, [], {"user_id": u"xxx@gmail.com", "display_name": u"XX FF"})
        except EmailException as e:
            print e
            raise

        res = email.to_browser(with_body=True)
        with open(os.path.join(getdir(__file__), "test_cases", test_case["expected_json"])) as f:
            obj = simplejson.load(f)

        expected_atts = obj.get("attachments", [])
        parsed_atts = res.get("attachments", [])
        assert len(expected_atts) == len(parsed_atts)
        for att in expected_atts:
            found = filter(
              lambda item: simplejson.dumps(item, sort_keys=True, indent=2) ==
              simplejson.dumps(att, sort_keys=True, indent=2),
              parsed_atts
            )
            assert len(found) == 1
