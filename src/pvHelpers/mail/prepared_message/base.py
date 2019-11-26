

from pvHelpers.crypto import PVKeyFactory, SYMM_KEY_PROTOCOL_VERSION
from pvHelpers.mail.email import EmailBase
from pvHelpers.user import LocalUser
from pvHelpers.utils import params


class PreparedMessageBase(object):
    """PreparedMessage factory class"""

    __initialized = False
    @params(object, LocalUser, EmailBase)
    def __init__(self, sender, email):
        self.sender = sender
        self.email = email
        self.attachments = []
        self.uploads = {}
        self.body = {}
        self.private_metadata = {}
        self.opaque_key = PVKeyFactory.new_symm_key(SYMM_KEY_PROTOCOL_VERSION.Latest)

        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(
                u"PreparedMessage has not have an attribute {}".format(key))
        object.__setattr__(self, key, value)
