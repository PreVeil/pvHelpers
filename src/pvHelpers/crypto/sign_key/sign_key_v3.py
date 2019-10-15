import types

import fipscrypto as FC
from pvHelpers.crypto.utils import (CURVE25519_PUB_KEY_LENGTH,
                                    EC_SECRET_LENGTH, NISTP256_PUB_KEY_LENGTH,
                                    CryptoException)
from pvHelpers.protos import Key as KeyBuffer
from pvHelpers.utils import b64enc, params

from .sign_key_base import SignKeyBase, VerifyKeyBase


class VerifyKeyV3(VerifyKeyBase):
    protocol_version = 3


    @params(object, bytes)
    def __init__(self, key):
        super(VerifyKeyV3, self).__init__(self.protocol_version)
        if len(key) != CURVE25519_PUB_KEY_LENGTH + NISTP256_PUB_KEY_LENGTH:
            raise CryptoException('invalid public `key` length {}'.format(len(key)))

        self.curve25519_pub = key[:CURVE25519_PUB_KEY_LENGTH]
        self.p256_pub = key[CURVE25519_PUB_KEY_LENGTH:]


    @property
    def key(self):
        return self.curve25519_pub + self.p256_pub


    @params(object, bytes, bytes)
    def verify(self, message, signature):
        return FC.hybrid_verify(self.curve25519_pub, self.p256_pub, signature, message)


    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.key
        )


    def serialize(self):
        b64 = b64enc(self.buffer.SerializeToString())
        return b64


class SignKeyV3(SignKeyBase):
    protocol_version = 3
    public_side_model = VerifyKeyV3


    @params(object, {bytes, types.NoneType})
    def __init__(self, key=None):
        super(SignKeyV3, self).__init__(self.protocol_version)
        if key is None:
            self._curve25519_secret, curve25519_pub = FC.generate_ec_key(
                FC.EC_KEY_TYPE.CURVE_25519, FC.EC_KEY_USAGE.SIGNATURE_USAGE)

            self._p256_secret, p256_pub = FC.generate_ec_key(
                FC.EC_KEY_TYPE.NIST_P256, FC.EC_KEY_USAGE.SIGNATURE_USAGE)

        else:
            if len(key) != 2 * EC_SECRET_LENGTH:
                raise CryptoException('invalid `key` length {}'.format(len(key)))

            self._curve25519_secret = key[:EC_SECRET_LENGTH]
            curve25519_pub = FC.ec_key_to_public(
                self._curve25519_secret, FC.EC_KEY_TYPE.CURVE_25519, FC.EC_KEY_USAGE.SIGNATURE_USAGE)
            self._p256_secret = key[EC_SECRET_LENGTH:]
            p256_pub = FC.ec_key_to_public(
                self._p256_secret, FC.EC_KEY_TYPE.NIST_P256, FC.EC_KEY_USAGE.SIGNATURE_USAGE)

        self._verify_key = self.public_side_model(curve25519_pub + p256_pub)


    @property
    def key(self):
        return self._curve25519_secret + self._p256_secret


    @property
    def verify_key(self):
        return self._verify_key


    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.key
        )


    def serialize(self):
        b64 = b64enc(self.buffer.SerializeToString())
        return b64


    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._curve25519_secret == other._curve25519_secret and \
            self._p256_secret == other._p256_secret


    def __ne__(self, other):
        return not self.__eq__(other)


    @params(object, bytes)
    def sign(self, message):
        return FC.hybrid_sign(self._curve25519_secret, self._p256_secret, message)
