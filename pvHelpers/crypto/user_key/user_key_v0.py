from ..asymm_key import AsymmKeyV0, PublicKeyV0
from ..sign_key import SignKeyV0, VerifyKeyV0
from .user_key_base import *
from ..utils import params, b64dec, CryptoException, g_log

class UserKeyV0(UserKeyBase):
    protocol_version = 0

    @params(object, int, AsymmKeyV0, SignKeyV0)
    def __init__(self, key_version, encryption_key=AsymmKeyV0(), signing_key=SignKeyV0()):
        super(UserKeyV0, self).__init__(self.protocol_version, key_version)
        self._encryption_key = encryption_key
        self._signing_key = signing_key
        self._public_user_key = PublicUserKeyV0(key_version, self._encryption_key.public_key, self._signing_key.verify_key)

    @property
    def encryption_key(self):
        return self._encryption_key

    @property
    def signing_key(self):
        return self._signing_key

    @property
    def public_user_key(self):
        return self._public_user_key

    @classmethod
    @params(object, {"private_key": unicode, "signing_key": unicode, "version": int})
    def fromDict(cls, key_dict):
        status, private_key = b64dec(key_dict["private_key"])
        if not status:
            raise CryptoException("Failed to b64 decrypt private_key")
        status, signing_key_seed = b64dec(key_dict["signing_key"])
        if not status:
            raise CryptoException("Failed to b64 decrypt signing_key_seed")

        return cls(key_dict["version"], AsymmKeyV0(private_key), SignKeyV0(signing_key_seed))

class PublicUserKeyV0(PublicUserKeyBase):
    protocol_version = 0

    @params(object, int, PublicKeyV0, VerifyKeyV0)
    def __init__(self, key_version, public_key, verify_key):
        super(PublicUserKeyV0, self).__init__(self.protocol_version, key_version)
        self._public_key = public_key
        self._verify_key = verify_key

    @property
    def public_key(self):
        return self._public_key

    @property
    def verify_key(self):
        return self._verify_key

    @classmethod
    @params(object, {"public_key": unicode, "verify_key": unicode, "version": int})
    def fromDict(cls, public_user_key_dict):
        status, public_key = b64dec(public_user_key_dict["public_key"])
        if not status:
            raise CryptoException("Failed to b64 decrypt public_key")
        status, verify_key = b64dec(public_user_key_dict["verify_key"])
        if not status:
            raise CryptoException("Failed to b64 decrypt verify_key")

        return cls(public_user_key_dict["version"], PublicKeyV0(public_key), VerifyKeyV0(verify_key))
