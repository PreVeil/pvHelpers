from .user_key_v0 import PublicUserKeyV0, UserKeyV0
from ..asymm_key import PublicKeyBase, AsymmKeyBase
from ..sign_key import SignKeyBase, VerifyKeyBase
from ..utils import params, UserKeyBuffer, PublicUserKeyBuffer, b64enc, g_log, utf8Encode, jdumps


class PublicUserKeyV1(PublicUserKeyV0):
    protocol_version = 1


    @params(object, {int, long}, PublicKeyBase, VerifyKeyBase)
    def __init__(self, key_version, public_key, verify_key):
        super(PublicUserKeyV1, self).__init__(key_version, public_key, verify_key)


    @property
    def buffer(self):
        return PublicUserKeyBuffer(
            protocol_version=self.protocol_version,
            key_version=self.key_version,
            public_key=self.public_key.buffer,
            verify_key=self.verify_key.buffer
        )


    def serialize(self):
        b64 = b64enc(self.buffer.SerializeToString())
        return b64


class UserKeyV1(UserKeyV0):
    protocol_version = 1
    public_side_model = PublicUserKeyV1


    @params(object, {int, long}, AsymmKeyBase, SignKeyBase)
    def __init__(self, key_version, encryption_key, signing_key):
        super(UserKeyV1, self).__init__(key_version, encryption_key, signing_key)


    @property
    def buffer(self):
        return UserKeyBuffer(
            protocol_version = self.protocol_version,
            key_version = self.key_version,
            private_key=self.encryption_key.buffer,
            signing_key=self.signing_key.buffer
        )


    def serialize(self):
        b64 = b64enc(self.buffer.SerializeToString())
        return b64


    def toDB(self):
        return self.serialize()
