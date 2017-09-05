import types
from .email_helpers import EmailException

class Content(object):
    def __init__(self, content=None, reference_id=None, block_ids=None):
        if not isinstance(content, (bytes, str, types.NoneType)):
            raise EmailException(u"Content.__init__: content must be of type bytes/str/None")
        self.content = content
        if not isinstance(reference_id, (unicode, types.NoneType)):
            raise EmailException(u"Content.__init__: reference_id must be of type unicode/None")
        self.reference_id = reference_id
        if not isinstance(block_ids, (list, types.NoneType)):
            raise EmailException(u"Content.__init__: block_ids must be of type list")
        self.block_ids = block_ids

    def toDict(self):
        return {
            "content": self.content,
            "reference_id": self.reference_id,
            "block_ids": self.block_ids
        }

    def isLoaded(self):
        return self.content != None

# class ServerContent(object):
#     def __init__(self, block_ids, fetcher_handle):
#         if not isinstance(block_ids, list):
#             raise TypeError(u"block_ids must be of type list")
#         for _id in block_ids:
#             if not isinstance(_id, unicode):
#                 raise TypeError(u"block_id must be of type unicode")
#         self.block_ids = block_ids
#
#         # fetcher's supposed to take the block_ids and return the content
#         if not isinstance(fetcher_handle, callable):
#             raise TypeError(u"fetcher_handle must be of type callable")
#         self._handle = fetcher_handle
#
#     def content(self):
#         # this should possibly to the decryption and ...
#         return self._handle(self.block_ids)
#
#
# class LocalContent(object):
#     def __init__(self, referece_id, fetcher_handle):
#         if not isinstance(referece_id, unicode):
#             raise TypeError(u"referece_id must be of type unicode")
#         self.referece_id = referece_id
#
#         # fetcher's supposed to take the block_ids and return the content
#         if not isinstance(fetcher_handle, callable):
#             raise TypeError(u"fetcher_handle must be of type callable")
#         self._handle = fetcher_handle
#
#     def content(self):
#         return self._handle(self.referece_id)
