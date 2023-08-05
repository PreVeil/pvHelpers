from __future__ import absolute_import
import struct, types, libnacl
from .asymm_key_v0 import AsymmKeyV0, PublicKeyV0
from ..utils import CryptoException, params, g_log, Sha512Sum, RandomBytes, KeyBuffer, b64enc


class PublicKeyV1(PublicKeyV0):
    protocol_version = 1


    @params(object, bytes)
    def __init__(self, public_key):
        super(PublicKeyV1, self).__init__(public_key)


    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self._public_key.pk
        )


    def serialize(self):
        b64_enc_public_key = b64enc(self.buffer.SerializeToString())
        return b64_enc_public_key


class AsymmKeyV1(AsymmKeyV0):
    protocol_version = 1
    public_side_model = PublicKeyV1


    @params(object, {bytes, type(None)})
    def __init__(self, key=None):
        super(AsymmKeyV1, self).__init__(key)


    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.sk
        )


    def serialize(self):
        b64_enc_private_key = b64enc(self.buffer.SerializeToString())
        return b64_enc_private_key
