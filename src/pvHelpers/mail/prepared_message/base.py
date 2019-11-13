

from pvHelpers.crypto import (ASYMM_KEY_PROTOCOL_VERSION,
                              SYMM_KEY_PROTOCOL_VERSION, PVKeyFactory)
from pvHelpers.crypto.utils import CryptoException
from pvHelpers.mail.email import EmailBase
from pvHelpers.user import LocalUser, User
from pvHelpers.utils import b64enc, params

from .helpers import PreparedMessageError


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
        self.opaque_key = PVKeyFactory.newSymmKey(SYMM_KEY_PROTOCOL_VERSION.Latest)

        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(
                u"PreparedMessage has not have an attribute {}".format(key))
        object.__setattr__(self, key, value)
