import types
from ..asymm_key import AsymmKeyV0, PublicKeyV0, AsymmKeyBase, PublicKeyBase
from ..sign_key import SignKeyV0, VerifyKeyV0, SignKeyBase, VerifyKeyBase
from .user_key_base import *
from ..utils import params, b64dec, CryptoException, g_log, utf8Encode, b64enc, utf8Decode, jloads


class PublicUserKeyV0(PublicUserKeyBase):
    protocol_version = 0


    @params(object, {int, long}, PublicKeyBase, VerifyKeyBase)
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


    def serialize(self):
        return jdumps({
            "public_key": self.public_key.serialize(),
            "verify_key": self.verify_key.serialize(),
            "version": self.key_version,
            "protocol_version": self.protocol_version
        })


    @classmethod
    @params(object, unicode)
    def deserialize(cls, json_serialized):
        status, public_user_key_dict = jloads(json_serialized)
        if not status:
            raise CryptoException("Failed to jload json_serialized")
        public_key = b64dec(public_user_key_dict["public_key"])
        verify_key = b64dec(public_user_key_dict["verify_key"])
        return cls(public_user_key_dict["version"], PublicKeyV0(public_key), VerifyKeyV0(verify_key))


class UserKeyV0(UserKeyBase):
    protocol_version = 0
    public_side_model = PublicUserKeyV0


    @params(object, {int, long}, AsymmKeyBase, SignKeyBase)
    def __init__(self, key_version, encryption_key, signing_key):
        super(UserKeyV0, self).__init__(self.protocol_version, key_version)
        self._encryption_key = encryption_key
        self._signing_key = signing_key
        self._public_user_key = self.public_side_model(key_version, self._encryption_key.public_key, self._signing_key.verify_key)


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
    @params(object, unicode)
    def deserialize(cls, b64):
        encoded = b64dec(b64)
        json_serialized = utf8Decode(encoded)
        status, key_dict = jloads(json_serialized)
        if not status:
            raise CryptoException("Failed to jload json_serialized")
        private_key = b64dec(key_dict["private_key"])
        signing_key_seed = b64dec(key_dict["signing_key"])
        return cls(key_dict["version"], AsymmKeyV0(private_key), SignKeyV0(signing_key_seed))


    def __ne__(self, other):
        return not self.__eq__(other)


    def __eq__(self, other):
        return self.key_version == other.key_version and \
            self._encryption_key == other.encryption_key and \
            self._signing_key == other.signing_key


    def serialize(self):
        json_serialized = jdumps({
            "private_key": self.encryption_key.serialize(),
            "signing_key": self.signing_key.serialize(),
            "version": self.key_version,
            "protocol_version": self.protocol_version
        })
        encoded = utf8Encode(json_serialized)
        b64 = b64enc(encoded)
        return b64


    def toDB(self):
        return jdumps({
            "private_key": self.encryption_key.serialize(),
            "signing_key": self.signing_key.serialize(),
            "version": self.key_version,
            "protocol_version": self.protocol_version
        })


    @classmethod
    def fromDB(cls, json_serialized):
        status, key_dict = jloads(json_serialized)
        if not status:
            raise CryptoException("Failed to jload json_serialized")
        private_key = b64dec(key_dict["private_key"])
        signing_key_seed = b64dec(key_dict["signing_key"])
        return cls(key_dict["version"], AsymmKeyV0(private_key), SignKeyV0(signing_key_seed))
