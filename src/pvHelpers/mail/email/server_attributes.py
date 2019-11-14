import types

from pvHelpers.utils import params


class ServerAttributes(object):
    __initialized = False

    @params(object, unicode, {unicode, types.NoneType}, {int, types.NoneType},
            {unicode, types.NoneType}, {unicode, types.NoneType}, {unicode, types.NoneType},
            {int, types.NoneType}, {unicode, types.NoneType}, {int, types.NoneType},
            {int, long, bool, types.NoneType})
    def __init__(self, server_id, collection_id, revision_id=None,
                 mailbox_server_id=None, mailbox_name=None, version=None,
                 uid=None, thread_id=None, server_time=None, expunged=None):
        self.server_id = server_id
        self.collection_id = collection_id
        self.revision_id = revision_id
        self.mailbox_server_id = mailbox_server_id
        self.mailbox_name = mailbox_name
        self.version = version
        self.uid = uid
        self.thread_id = thread_id
        self.server_time = server_time

        # TODO: Values are stored as `int`, need to correct DB inserts after schema update (full refetch)
        if expunged is not None:
            expunged = bool(expunged)
        self.expunged = expunged

        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"ServerAttributes has not attribute {}".format(key))
        object.__setattr__(self, key, value)

    def to_dict(self):
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
