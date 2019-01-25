import types
from .sign_key_base import SignKeyBase, VerifyKeyBase
from ..utils import KeyBuffer, b64enc, params, b64dec, CryptoException, utf8Decode, utf8Encode
import fipscrypto as FC


class VerifyKeyV3(VerifyKeyBase):
    protocol_version = 3

    @params(object, bytes, bytes)
    def __init__(self, curve25519_pub, p256_pub):
        super(VerifyKeyV3, self).__init__(self.protocol_version)
        self.curve25519_pub = curve25519_pub
        self.p256_pub = p256_pub

    @params(object, bytes, unicode)
    def verifyBinary(self, message, signature):
        status, signature = b64dec(signature)
        if not status:
            raise CryptoException("Failed to b64 decode signature")

        return FC.hybrid_verify(self.curve25519_pub, self.p256_pub, signature, message)

    @params(object, unicode, unicode)
    def verifyText(self, message, signature):
        status, raw_message = utf8Encode(message)
        if not status:
            raise CryptoException("Failed to utf8 encode message")
        return self.verifyBinary(raw_message, signature)

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.curve25519_pub + self.p256_pub
        )

    def serialize(self):
        return self.buffer.SerializeToString()


class SignKeyV3(SignKeyBase):
    protocol_version = 3
    public_side_model = VerifyKeyV3

    @params(object, {bytes, types.NoneType}, {bytes, types.NoneType})
    def __init__(self, curve25519_secret=None, p256_secret=None):
        super(SignKeyV3, self).__init__(self.protocol_version)
        if curve25519_secret is None and p256_secret is None:
            self._curve25519_secret, curve25519_pub = FC.generate_ec_key(
                FC.EC_KEY_TYPE.CURVE_25519, FC.EC_KEY_USAGE.SIGNATURE_USAGE)

            self._p256_secret, p256_pub = FC.generate_ec_key(
                FC.EC_KEY_TYPE.NIST_P256, FC.EC_KEY_USAGE.SIGNATURE_USAGE)

        else:
            self._curve25519_secret = curve25519_secret
            curve25519_pub = FC.ec_key_to_public(
                self._curve25519_secret, FC.EC_KEY_TYPE.CURVE_25519, FC.EC_KEY_USAGE.SIGNATURE_USAGE)
            self._p256_secret = p256_secret
            p256_pub = FC.ec_key_to_public(
                self._p256_secret, FC.EC_KEY_TYPE.NIST_P256, FC.EC_KEY_USAGE.SIGNATURE_USAGE)

        self._verify_key = self.public_side_model(curve25519_pub, p256_pub)

    @property
    def verify_key(self):
        return self._verify_key

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self._curve25519_secret + self._p256_secret
        )

    def serialize(self):
        return self.buffer.SerializeToString()

    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._curve25519_secret == other._curve25519_secret and \
            self._p256_secret == other._p256_secret

    def __ne__(self, other):
        return not self.__eq__(other)


    @params(object, bytes)
    def signBinary(self, message):
        status, b64_signature = b64enc(FC.hybrid_sign(self._curve25519_secret, self._p256_secret, message))
        if not status:
            raise CryptoException("Failed to b64 encode signature")
        return b64_signature

    @params(object, unicode)
    def signText(self, message):
        status, raw_message = utf8Encode(message)
        if not status:
            raise CryptoException("Failed to utf8 encode message")

        return self.signBinary(raw_message)
