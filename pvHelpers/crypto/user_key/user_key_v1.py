from ..asymm_key import AsymmKeyV1, PublicKeyV1
from ..sign_key import SignKeyV0, VerifyKeyV0
from .user_key_base import *
from ..utils import params

class UserKeyV1(UserKeyBase):
    protocol_version = 1

    @params(object, int, AsymmKeyV1, SignKeyV0)
    def __init__(self, key_version, encryption_key, signing_key):
        super(UserKeyV0, self).__init__(self.protocol_version, key_version)
        self._encryption_key = encryption_key
        self._signing_key = signing_key

    @property
    def encryption_key(self):
        return self._encryption_key

    @property
    def signing_key(self):
        return self._signing_key

    # @classmethod
    # def deserialize(cls, data):
    #     return cls(1, UserKeyV1)


class PublicUserKeyV1(PublicUserKeyBase):
    protocol_version = 1

    @params(object, int, PublicKeyV1, VerifyKeyV0)
    def __init__(self, key_version, public_key, verify_key):
        super(UserPublicKeyV1, self).__init__(self.protocol_version, key_version)
        self.public_key = public_key
        self.verify_key = verify_key

    @classmethod
    @params(object, {"public_key": unicode, "verify_key": unicode, "version": int})
    def deserialize(cls, public_user_key_dict):
        pass
