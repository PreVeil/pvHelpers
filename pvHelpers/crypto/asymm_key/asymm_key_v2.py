from __future__ import absolute_import
import struct, types, libnacl
from .asymm_key_v0 import AsymmKeyV0, PublicKeyV0
from ..utils import CryptoException, params, g_log, Sha512Sum, RandomBytes, KeyBuffer, b64enc


crypto_box_SEEDBYTES = libnacl.nacl.crypto_box_seedbytes()


class PublicKeyV2(PublicKeyV0):
    protocol_version = 2


    @params(object, bytes)
    def __init__(self, public_key):
        super(PublicKeyV2, self).__init__(public_key)


    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self._public_key.pk
        )


    def serialize(self):
        b64_enc_public_key = b64enc(self.buffer.SerializeToString())
        return b64_enc_public_key


class AsymmKeyV2(AsymmKeyV0):
    protocol_version = 2
    public_side_model = PublicKeyV2


    @params(object, {bytes, type(None)})
    def __init__(self, key=None):
        if not key:
            key = RandomBytes(crypto_box_SEEDBYTES)
        if len(key) != crypto_box_SEEDBYTES:
            raise CryptoException(u"invalid seed")

        self._seed = key
        super(AsymmKeyV2, self).__init__(Sha512Sum(self._seed)[:32])


    @property
    def key(self):
        return self._seed


    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self._seed
        )


    @property
    def seed(self):
        return self._seed


    def serialize(self):
        b64_enc_private_key = b64enc(self.buffer.SerializeToString())
        return b64_enc_private_key
