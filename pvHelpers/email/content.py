import types
import email_helpers
from ..params import params


class Content(object):
    __initialized = False
    @params(object, {bytes, str, types.NoneType}, [unicode], {unicode, types.NoneType}, {int, long, types.NoneType})
    def __init__(self, content=None, block_ids=[], wrapped_key=None, key_version=None):
        self.content = content
        self.block_ids = block_ids
        self.wrapped_key = wrapped_key
        self.key_version = key_version
        if content is None:
            if wrapped_key is None or key_version is None:
                raise email_helpers.EmailException(u"Contet should either have data or the associated wrapped_key/key_version")
        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"Content has not attribute {}".format(key))
        object.__setattr__(self, key, value)

    def toDict(self):
        return {
            "content": self.content,
            "block_ids": self.block_ids,
            "wrapped_key": self.wrapped_key,
            "key_version": self.key_version
        }

    @property
    def reference_id(self):
        return u",".join(self.block_ids)

    def isLoaded(self):
        return self.content != None
