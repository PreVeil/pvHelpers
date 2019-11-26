import types

import libnacl
import libnacl.sign
from pvHelpers.crypto.utils import CryptoException, hex_encode
from pvHelpers.utils import b64enc, params

from .base import SignKeyBase, VerifyKeyBase


class VerifyKeyV0(VerifyKeyBase):
    protocol_version = 0

    @params(object, bytes)
    def __init__(self, verifier_key):
        super(VerifyKeyV0, self).__init__(self.protocol_version)
        self._verifier = libnacl.sign.Verifier(hex_encode(verifier_key))

    @property
    def key(self):
        return self._verifier.vk

    @property
    def vk(self):
        return self._verifier.vk

    @params(object, bytes, bytes)
    def verify(self, message, signature):
        try:
            self._verifier.verify(signature + message)
        except ValueError as e:
            return False
        except libnacl.CryptError as e:
            raise CryptoException(e)
        return True

    def serialize(self):
        b64_enc_verify_key = b64enc(self._verifier.vk)
        return b64_enc_verify_key


class SignKeyV0(SignKeyBase):
    protocol_version = 0
    public_side_model = VerifyKeyV0

    @params(object, {bytes, types.NoneType})
    def __init__(self, key=None):
        super(SignKeyV0, self).__init__(self.protocol_version)
        self._signer = libnacl.sign.Signer(key)
        self._verify_key = self.public_side_model(self._signer.vk)

    @property
    def key(self):
        return self._signer.seed

    @property
    def verify_key(self):
        return self._verify_key

    @property
    def seed(self):
        return self._signer.seed

    def serialize(self):
        b64_enc_signing_seed = b64enc(self._signer.seed)
        return b64_enc_signing_seed

    @params(object, bytes)
    def sign(self, message):
        return self._signer.signature(message)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        return self._signer.seed == other.seed
