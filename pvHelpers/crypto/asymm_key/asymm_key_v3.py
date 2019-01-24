import types, struct
from ..utils import params, b64enc, b64dec, utf8Decode, utf8Encode, KeyBuffer
from .asymm_key_base import PublicKeyBase, AsymmKeyBase
from .asymm_key_v0 import BINARY_BIT, TEXT_BIT, ASYMM_BIT, SEAL_BIT
import fipscrypto as FC

class PublicKeyV3(PublicKeyBase):
    protocol_version = 3

    @params(object, bytes, bytes)
    def __init__(self, curve25519_pub, p256_pub):
        super(PublicKeyV3, self).__init__(self.protocol_version)
        self.curve25519_pub = curve25519_pub
        self.p256_pub = p256_pub


    @params(object, bytes)
    def sealBinary(self, message):
        message_with_header = struct.pack(">BBBB", BINARY_BIT | SEAL_BIT, 0x00, 0x00, 0x00) + message
        sealed_message = FC.hybrid_seal(self.curve25519_pub, self.p256_pub, message_with_header)
        status, b64 = b64enc(sealed_message)
        if not status:
            raise CryptoException("Failed to b64 encode message")
        return b64

    @params(object, unicode)
    def sealText(self, message):
        status, raw_message = utf8Encode(message)
        if not status:
            raise CryptoException("Failed to utf8 encode message")
        message_with_header = struct.pack(">BBBB", TEXT_BIT | SEAL_BIT, 0x00, 0x00, 0x00) + raw_message
        sealed_message = FC.hybrid_seal(self.curve25519_pub, self.p256_pub, message_with_header)
        status, b64 = b64enc(sealed_message)
        if not status:
            raise CryptoException("Failed to b64 encode message")
        return b64

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.curve25519_pub + self.p256_pub
        )

    def serialize(self):
        return self.buffer.SerializeToString()


class AsymmKeyV3(AsymmKeyBase):
    protocol_version = 3
    public_side_model = PublicKeyV3

    @params(object, {bytes, types.NoneType}, {bytes, types.NoneType})
    def __init__(self, curve25519_secret=None, p256_secret=None):
        super(AsymmKeyV3, self).__init__(self.protocol_version)
        if curve25519_secret is None and p256_secret is None:
            self._curve25519_secret, curve25519_pub = FC.generate_ec_key(
                FC.EC_KEY_TYPE.CURVE_25519, FC.EC_KEY_USAGE.ENCRYPTION_USAGE)

            self._p256_secret, p256_pub = FC.generate_ec_key(
                FC.EC_KEY_TYPE.NIST_P256, FC.EC_KEY_USAGE.ENCRYPTION_USAGE)

        else:
            self._curve25519_secret = curve25519_secret
            curve25519_pub = FC.ec_key_to_public(
                self._curve25519_secret, FC.EC_KEY_TYPE.CURVE_25519, FC.EC_KEY_USAGE.ENCRYPTION_USAGE)
            self._p256_secret = p256_secret
            p256_pub = FC.ec_key_to_public(
                self._p256_secret, FC.EC_KEY_TYPE.NIST_P256, FC.EC_KEY_USAGE.ENCRYPTION_USAGE)

        self._public_key = self.public_side_model(curve25519_pub, p256_pub)

    @property
    def public_key(self):
        return self._public_key

    @params(object, unicode)
    def unsealBinary(self, cipher):
        status, cipher = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")
        message_with_header = FC.hybrid_unseal(self._curve25519_secret, self._p256_secret, cipher)
        header = struct.unpack(">BBBB", message_with_header[:4])
        if header[0] != (BINARY_BIT | SEAL_BIT):
            raise CryptoException(u"Invalid header bytes")
        return message_with_header[4:]

    @params(object, unicode)
    def unsealText(self, cipher):
        status, cipher = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")
        message_with_header = FC.hybrid_unseal(self._curve25519_secret, self._p256_secret, cipher)
        header = struct.unpack(">BBBB", message_with_header[:4])
        if header[0] != (TEXT_BIT | SEAL_BIT):
            raise CryptoException(u"Invalid header bytes")
        status, message = utf8Decode(message_with_header[4:])
        if not status:
            raise CryptoException(u"Failed to utf8 decode message")
        return message

    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._curve25519_secret == other._curve25519_secret and \
            self._p256_secret == other._p256_secret

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self._curve25519_secret + self._p256_secret
        )

    def serialize(self):
        return self.buffer.SerializeToString()
