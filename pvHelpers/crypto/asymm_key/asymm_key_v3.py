from ..utils import params
from .asymm_key_base import PublicKeyBase, AsymmKeyBase


class PublicKeyV3(PublicKeyBase):
    protocol_version = 3

    @params(object)
    def __init__(self):
        super(PublicKeyV3, self).__init__(protocol_version)


class AsymmKeyV3(AsymmKeyBase):
    protocol_version = 3
    public_side_model = PublicKeyV3

    @params(object, bytes, bytes)
    def __init__(self, curve25519_secret, p256_secret):
        super(AsymmKeyV3, self).__init__(self.protocol_version)
