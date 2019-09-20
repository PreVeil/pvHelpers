

from pvHelpers.crypto import (ASYMM_KEY_PROTOCOL_VERSION,
                              SYMM_KEY_PROTOCOL_VERSION, CryptoException,
                              PVKeyFactory)
from pvHelpers.mail.email import EmailBase
from pvHelpers.user import LocalUser, User
from pvHelpers.utils import b64enc, params

from .prepared_message_helpers import PreparedMessageError


#########################################
########### Factory Base Class ##########
#########################################
class PreparedMessageBase(object):
    __initialized = False
    @params(object, LocalUser, EmailBase, User)
    def __init__(self, sender, email, recipient):
        self.sender = sender
        self.recipient = recipient
        self.email = email
        self.attachments = []
        self.uploads = {}
        self.body = {}
        self.private_metadata = {}
        try:
            self.opaque_key = PVKeyFactory.newSymmKey(
                SYMM_KEY_PROTOCOL_VERSION.Latest)
            if self.recipient.public_user_key.public_key.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V3:
                self.sealed_opaque_key = b64enc(self.recipient.public_user_key.public_key.seal(
                    self.opaque_key.serialize()))
            else:
                self.sealed_opaque_key = b64enc(self.recipient.public_user_key.public_key.seal(
                    self.opaque_key.serialize(), is_text=True))
        except CryptoException as e:
            raise PreparedMessageError(e)

        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(
                u"PreparedMessage has not have an attribute {}".format(key))
        object.__setattr__(self, key, value)
