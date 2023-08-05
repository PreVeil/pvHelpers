from __future__ import absolute_import
import types
from . import email_helpers
from ..params import params
import six


class Content(object):
    __initialized = False

    @params(object, {bytes, str, type(None)}, [six.text_type],
            {six.text_type, type(None)}, {int, int, type(None)},
            {int, int, type(None)})
    def __init__(self, content=None, block_ids=[], wrapped_key=None, key_version=None, size=None):
        self.content = content
        self.block_ids = block_ids
        self.wrapped_key = wrapped_key
        self.key_version = key_version
        self._size = size
        if content is None:
            if wrapped_key is None or key_version is None:
                raise email_helpers.EmailException(u"Content should either have data or the associated wrapped_key/key_version")
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
            "key_version": self.key_version,
            "size": self.size
        }

    @property
    def reference_id(self):
        return u",".join(self.block_ids)

    def isLoaded(self):
        return self.content is not None

    @property
    def size(self):
        s = len(self.content) if self.content else self._size
        if not s:
            return 0
        return s
