import pvHelpers as H

from .prepared_message_helpers import PreparedMessageError


#########################################
########### Factory Base Class ##########
#########################################
class PreparedMessageBase(object):
    __initialized = False
    @H.params(object, H.LocalUser, H.EmailBase, H.User)
    def __init__(self, sender, email, recipient):
        self.sender = sender
        self.recipient = recipient
        self.email = email
        self.attachments = []
        self.uploads = {}
        self.body = {}
        self.private_metadata = {}
        try:
            self.opaque_key = H.PVKeyFactory.newSymmKey(
                H.SYMM_KEY_PROTOCOL_VERSION.Latest)
            if self.recipient.public_user_key.public_key.protocol_version == H.ASYMM_KEY_PROTOCOL_VERSION.V3:
                self.sealed_opaque_key = H.b64enc(self.recipient.public_user_key.public_key.seal(
                    self.opaque_key.serialize()))
            else:
                self.sealed_opaque_key = H.b64enc(self.recipient.public_user_key.public_key.seal(
                    self.opaque_key.serialize(), is_text=True))
        except H.CryptoException as e:
            raise PreparedMessageError(e)

        self.__initialized = True

    def __setattr__(self, key, value):
        if self.__initialized and not hasattr(self, key):
            raise KeyError(
                u"PreparedMessage has not have an attribute {}".format(key))
        object.__setattr__(self, key, value)
