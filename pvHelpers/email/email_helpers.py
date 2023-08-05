from __future__ import absolute_import
from ..misc import jdumps, jloads, utf8Decode, encodeContentIfUnicode, EncodingException
from pvHelpers.hook_decorators import WrapExceptions
import uuid
from pvHelpers.params import params


DUMMY_DISPOSITION = u"dummy"
DUMMY_CONTENT_TYPE = u"dummy/dummy"
MAILBOX_ALIAS = {u"INBOX": u"inbox", u"Drafts": u"drafts", u"Sent Messages": u"sent", u"Deleted Messages": u"trash"}


class PROTOCOL_VERSION(object):
    """This protocol version represents the structure of a prepared message, which indicates
    how it should be parsed.
    """
    V1 = 1
    V2 = 2
    V3 = 3
    V4 = 4
    V5 = 5
    V6 = 6
    V7 = 7
    Latest = 7


class EmailRecipients():
    Tos = u"Tos"
    Bccs = u"Bccs"
    Ccs = u"Ccs"


class EmailException(Exception):
    def __init__(self, message=u""):
        Exception.__init__(self, message)


#########################################
######### Factory Common Mixins #########
#########################################
class EmailHelpers(object):
    # FIXME: this works when we only have aliases for the 4 default maiboxes,
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
    @WrapExceptions(EmailException, [EncodingException])
    @params(dict)
    def serializeBody(body):
        return encodeContentIfUnicode(jdumps({"text": body.get("text"), "html": body.get("html")}))

    @staticmethod
    @WrapExceptions(EmailException, [EncodingException])
    @params(bytes)
    def deserializeBody(body):
        body = jloads(utf8Decode(body))
        return body

    @staticmethod
    def isLocalEmail(email_id):
        return email_id.startswith(u"__local__")


    @staticmethod
    @params(dict)
    def format_recip(recip):
        if "members" in recip:
            # group recipient
            return {
                "user_id": recip["user_id"],
                "display_name": recip["user_id"],
                "external_email": recip.get(u"external_email", None),
                "members": recip["members"]
            }
        elif recip.get(u"external_email") is None:
            return {
                "user_id": recip["user_id"],
                "display_name": recip["user_id"]
            }
        else:
            return {
                "user_id": recip["user_id"],
                "display_name": recip["external_email"],
                "external_email": recip["external_email"]
            }

    @staticmethod
    @params(dict)
    def format_ext_disp(recipient):
        if "external_email" in recipient and recipient["external_email"] is not None:
            return {"user_id": recipient["user_id"], "display_name": u"[External] " + recipient["display_name"], "external_email": recipient["external_email"]}
        else:
            return {"user_id": recipient["user_id"], "display_name": recipient["display_name"]}