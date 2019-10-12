from pvHelpers import randUnicode

from random import randint


def recipient():
    return {"user_id": randUnicode(5), "key_version": randint(0, 100)}


class MockServerMessageBase(object):
    def __init__(self, protocol_version, private_metadata):
        self.protocol_version = protocol_version
        self.private_metadata = private_metadata
        self.id = randUnicode(5)
        self.version = randUnicode(5)
        self.thread_id = randUnicode(5)
        self.mailbox_id = randUnicode(5)

        self.uid = 0
        self.message_id = randUnicode(5)

        self.in_reply_to = randUnicode(5)
        self.rev_id = 0
        self.is_deleted = False
        self.references = []
        self.flags = []
        self.timestamp = '2019-08-16T16:14:48'

    def toDict(self):
        return {
            "private_metadata": self.private_metadata,
            "protocol_version": self.protocol_version,
            "id": self.id,
            "version": self.version,
            "thread_id": self.thread_id,
            "mailbox_id": self.mailbox_id,
            "uid": self.uid,
            "message_id": self.message_id,
            "in_reply_to": self.in_reply_to,
            "rev_id": self.rev_id,
            "is_deleted": self.is_deleted,
            "references": self.references,
            "flags": self.flags,
            "timestamp": self.timestamp
        }
