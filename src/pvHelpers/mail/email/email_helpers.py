import uuid

import pvHelpers as H
from pvHelpers.utils import (EncodingException, WrapExceptions,
                             encodeContentIfUnicode, jdumps, jloads, params,
                             utf8Decode)


DUMMY_DISPOSITION = u"dummy"
DUMMY_CONTENT_TYPE = u"dummy/dummy"
MAILBOX_ALIAS = {u"INBOX":u"inbox", u"Drafts":u"drafts", u"Sent Messages":u"sent", u"Deleted Messages":u"trash"}

class PROTOCOL_VERSION(object):
    V1 = 1
    V2 = 2
    V3 = 3
    V4 = 4
    Latest = 4


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
