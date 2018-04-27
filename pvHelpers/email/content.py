import types
import email_helpers
from ..params import params

class ServerContent(object):
    __initialized = False
    @params(object, {bytes, str, types.NoneType}, {[unicode], types.NoneType})
    def __init__(self, content=None, block_ids=None):
        self.content = content
        self.block_ids = block_ids
        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"Content has not attribute {}".format(key))
        object.__setattr__(self, key, value)

    def toDict(self):
        return {
            "content": self.content,
            "block_ids": self.block_ids
        }

    def isLoaded(self):
        return self.content != None

class LocalContent(object):
    __initialized = False
    @params(object, {bytes, str, types.NoneType}, {unicode, types.NoneType})
    def __init__(self, content=None, reference_id=None):
        self.content = content
        self.reference_id = reference_id
        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"Content has not attribute {}".format(key))
        object.__setattr__(self, key, value)

    def toDict(self):
        return {
            "content": self.content,
            "reference_id": self.reference_id
        }

    def isLoaded(self):
        return self.content != None
