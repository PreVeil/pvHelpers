import copy
import types

from pvHelpers.utils import NotAssigned, params

from .attachment import Attachment
from .content import Content
from .server_attributes import ServerAttributes


USER_INFO_TYPE = {"user_id": unicode, "display_name": unicode}


class EmailBase(object):
    """factory base class"""

    __initialized = False

    @params(object, {ServerAttributes, NotAssigned}, int, [unicode], [USER_INFO_TYPE],
            [USER_INFO_TYPE], [USER_INFO_TYPE], USER_INFO_TYPE, [USER_INFO_TYPE], unicode,
            Content, [Attachment], [unicode], {unicode, types.NoneType}, unicode, {unicode, types.NoneType})
    def __init__(self, server_attr, protocol_version, flags, tos, ccs, bccs,
                 sender, reply_tos, subject, body, attachments, references,
                 in_reply_to, message_id, snippet):
        self.server_attr = server_attr
        self.protocol_version = protocol_version
        self.flags = flags
        self.tos = tos
        self.ccs = ccs
        self.bccs = bccs
        self.sender = sender
        self.reply_tos = reply_tos
        self.subject = subject
        self.body = body
        self.attachments = attachments
        self.references = references
        self.in_reply_to = in_reply_to
        self.message_id = message_id
        self._snippet = snippet

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(u"EmailBase has not attribute {}".format(key))
        object.__setattr__(self, key, value)

    def __deepcopy__(self, memo):
        return self.__class__(**copy.deepcopy(self.to_dict()))

    def snippet(self):
        raise NotImplementedError(u"must be implemented by children classes")

    def to_browser(self):
        raise NotImplementedError(u"must be implemented by children classes")

    def to_mime(self):
        raise NotImplementedError(u"must be implemented by children classes")

    def to_dict(self):
        raise NotImplementedError(u"must be implemented by children classes")

    def load_body(self, content):
        self.body.content = content

    def indexable_attachment_names(self):
        raise NotImplementedError(u"must be implemented by children classes")

    def indexable_body(self):
        raise NotImplementedError(u"must be implemented by children classes")

    def indexable_recipients(self):
        raise NotImplementedError(u"must be implemented by children classes")
