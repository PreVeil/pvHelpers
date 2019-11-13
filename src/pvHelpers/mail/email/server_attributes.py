import types

from .email_helpers import EmailException


class ServerAttributes(object):
    __initialized = False

    def __init__(self, server_id, collection_id, revision_id=None,
                 mailbox_server_id=None, mailbox_name=None, version=None,
                 uid=None, thread_id=None, server_time=None, expunged=None):
        if not isinstance(server_id, unicode):
            raise EmailException(u"ServerAttributes.__init__: server_id must be of type unicode")
        self.server_id = server_id

        if not isinstance(collection_id, (unicode, types.NoneType)):
            raise EmailException(
                u"ServerAttributes.__init__: collection_id must be of type unicode")
        self.collection_id = collection_id

        if not isinstance(revision_id, (int, types.NoneType)):
            raise EmailException(u"ServerAttributes.__init__: revision_id must be of type int")
        self.revision_id = revision_id

        if not isinstance(mailbox_server_id, (unicode, types.NoneType)):
            raise EmailException(u"ServerAttributes.__init__: mailbox_server_id must be of type unicode")
        self.mailbox_server_id = mailbox_server_id

        if not isinstance(mailbox_name, (unicode, types.NoneType)):
            raise EmailException(u"ServerAttributes.__init__: mailbox_name must be of type unicode")
        self.mailbox_name = mailbox_name

        if not isinstance(version, (unicode, types.NoneType)):
            raise EmailException(u"ServerAttributes.__init__: version must be of type unicode")
        self.version = version

        if not isinstance(uid, (int, types.NoneType)):
            raise EmailException(u"ServerAttributes.__init__: uid must be of type int")
        self.uid = uid

        if not isinstance(thread_id, (unicode, types.NoneType)):
            raise EmailException(u"ServerAttributes.__init__: thread_id must be of type unicode")
        self.thread_id = thread_id

        if not isinstance(server_time, (int, types.NoneType)):
            raise EmailException(u"ServerAttributes.__init__: server_time must be of type int")
        self.server_time = server_time

        # TODO: Values are stored as `int`, need to correct DB inserts after schema update (full refetch)
        if isinstance(expunged, (int, long)):
            expunged = bool(expunged)
        if not isinstance(expunged, (bool, types.NoneType)):
            raise EmailException(u"ServerAttributes.__init__: expunged must be of type bool")
        self.expunged = expunged

        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"ServerAttributes has not attribute {}".format(key))
        object.__setattr__(self, key, value)

    def toDict(self):
        return {
            "server_id": self.server_id,
            "revision_id": self.revision_id,
            "mailbox_server_id": self.mailbox_server_id,
            "mailbox_name": self.mailbox_name,
            "version": self.version,
            "uid": self.uid,
            "thread_id": self.thread_id,
            "server_time": self.server_time,
            "expunged": self.expunged,
            "collection_id": self.collection_id
        }
