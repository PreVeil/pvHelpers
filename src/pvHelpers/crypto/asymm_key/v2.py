import types

import libnacl
from pvHelpers.crypto.utils import CryptoException, random_bytes, sha_512_sum
from pvHelpers.protos import Key as KeyBuffer
from pvHelpers.utils import b64enc, params

from .v0 import AsymmKeyV0, PublicKeyV0

CRYPTO_BOX_SEEDBYTES = libnacl.nacl.crypto_box_seedbytes()


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

    @params(object, {bytes, types.NoneType})
    def __init__(self, key=None):
        if not key:
            key = random_bytes(CRYPTO_BOX_SEEDBYTES)
        if len(key) != CRYPTO_BOX_SEEDBYTES:
            raise CryptoException(u"invalid seed")

        self._seed = key
        super(AsymmKeyV2, self).__init__(sha_512_sum(self._seed)[:32])

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
