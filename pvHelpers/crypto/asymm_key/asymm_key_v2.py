import struct, types, libnacl
from .asymm_key_v0 import AsymmKeyV0, PublicKeyV0
from ..utils import CryptoException, params, g_log, Sha512Sum, RandomBytes, KeyBuffer

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


class AsymmKeyV2(AsymmKeyV0):
    protocol_version = 2
    public_side_model = PublicKeyV2

    @params(object, {bytes, types.NoneType})
    def __init__(self, enc_seed=None):
        if not enc_seed:
            enc_seed = RandomBytes(crypto_box_SEEDBYTES)
        if len(enc_seed) != crypto_box_SEEDBYTES:
            raise CryptoException(u"invalid seed")

        self._seed = enc_seed
        super(AsymmKeyV2, self).__init__(Sha512Sum(enc_seed)[:32])

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self._seed
        )

    @property
    def seed(self):
        return self._seed
