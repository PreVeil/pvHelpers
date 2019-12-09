import uuid

from pvHelpers.utils import (encode_content_if_unicode, EncodingException,
                             jdumps, jloads, params, utf8_decode, WrapExceptions)


DUMMY_DISPOSITION = u"dummy"
DUMMY_CONTENT_TYPE = u"dummy/dummy"
MAILBOX_ALIAS = {
    u"INBOX": u"inbox",
    u"Drafts": u"drafts",
    u"Sent Messages": u"sent",
    u"Deleted Messages": u"trash"
}


class PROTOCOL_VERSION(object):  # noqa: N801
    """
    This protocol version represents the structure of a prepared message,
    which indicates how it should be parsed.
    """
    V1 = 1
    V2 = 2
    V3 = 3
    V4 = 4
    V5 = 5
    V6 = 6
    Latest = 6


class EmailRecipients():
    Tos = u"Tos"
    Bccs = u"Bccs"
    Ccs = u"Ccs"


class EmailException(Exception):
    def __init__(self, message=u""):
        Exception.__init__(self, message)


class EmailHelpers(object):
    """factory mixins"""

    # FIXME: this works when we only have aliases for the 4 default maiboxes,
    # and use the real "DB" mailbox_name for a custom mailbox
    @staticmethod
    def get_mailbox_alias(mailbox_name):
        if mailbox_name in MAILBOX_ALIAS:
            return MAILBOX_ALIAS[mailbox_name]
        return mailbox_name

    @staticmethod
    def new_message_id():
        return u"{}@preveil.com".format(str(uuid.uuid4()))

    @staticmethod
    @WrapExceptions(EmailException, [EncodingException])
    @params(dict)
    def serialize_body(body):
        return encode_content_if_unicode(jdumps({"text": body.get("text"), "html": body.get("html")}))

    @staticmethod
    @WrapExceptions(EmailException, [EncodingException])
    @params(bytes)
    def deserialize_body(body):
        body = jloads(utf8_decode(body))
        return body

    @staticmethod
    def is_local_email(email_id):
        return email_id.startswith(u"__local__")

    @staticmethod
    @params(dict)
    def format_recip(recip):
        if "members" in recip:
            # group recipient
            return {
                "user_id": recip["user_id"],
                "display_name": recip["user_id"],
                "members": recip["members"]
            }
        return {
            "user_id": recip["user_id"],
            "display_name": recip["user_id"]
        }
