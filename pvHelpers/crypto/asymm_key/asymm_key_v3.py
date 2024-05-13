import types
from ..utils import params, b64enc, b64dec, utf8Decode, utf8Encode, KeyBuffer, CryptoException, SealedDataBuffer, ProtobufErrors, \
    CURVE25519_PUB_KEY_LENGTH, NISTP256_PUB_KEY_LENGTH, EC_SECRET_LENGTH
from .asymm_key_base import PublicKeyBase, AsymmKeyBase
import fipscrypto as FC


class PublicKeyV3(PublicKeyBase):
    protocol_version = 3


    @params(object, bytes)
    def __init__(self, key):
        super(PublicKeyV3, self).__init__(self.protocol_version)
        if len(key) != CURVE25519_PUB_KEY_LENGTH + NISTP256_PUB_KEY_LENGTH:
            raise CryptoException('invalid public `key` length {}'.format(len(key)))

        self.curve25519_pub = key[:CURVE25519_PUB_KEY_LENGTH]
        self.p256_pub = key[CURVE25519_PUB_KEY_LENGTH:]


    @property
    def key(self):
        return self.curve25519_pub + self.p256_pub


    @params(object, bytes)
    def seal(self, message):
        ciphertext = FC.hybrid_seal(self.curve25519_pub, self.p256_pub, message, True)
        buffer = SealedDataBuffer(
            protocol_version=1,
            ciphertext=ciphertext,
            proof=1
        )
        return buffer.SerializeToString()


    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.key
        )


    def serialize(self):
        b64_enc_public_key = b64enc(self.buffer.SerializeToString())
        return b64_enc_public_key


class AsymmKeyV3(AsymmKeyBase):
    protocol_version = 3
    public_side_model = PublicKeyV3


    @params(object, {bytes, types.NoneType})
    def __init__(self, key=None):
        super(AsymmKeyV3, self).__init__(self.protocol_version)
        if key is None:
            self._curve25519_secret, curve25519_pub = FC.generate_ec_key(
                FC.EC_KEY_TYPE.CURVE_25519, FC.EC_KEY_USAGE.ENCRYPTION_USAGE)

            self._p256_secret, p256_pub = FC.generate_ec_key(
                FC.EC_KEY_TYPE.NIST_P256, FC.EC_KEY_USAGE.ENCRYPTION_USAGE)

        else:
            if len(key) != 2 * EC_SECRET_LENGTH:
                raise CryptoException('invalid `key` length {}'.format(len(key)))

            self._curve25519_secret = key[:EC_SECRET_LENGTH]
            curve25519_pub = FC.ec_key_to_public(
                self._curve25519_secret, FC.EC_KEY_TYPE.CURVE_25519, FC.EC_KEY_USAGE.ENCRYPTION_USAGE)
            self._p256_secret = key[EC_SECRET_LENGTH:]
            p256_pub = FC.ec_key_to_public(
                self._p256_secret, FC.EC_KEY_TYPE.NIST_P256, FC.EC_KEY_USAGE.ENCRYPTION_USAGE)

        self._public_key = self.public_side_model(curve25519_pub + p256_pub)


    @property
    def key(self):
        return self._curve25519_secret + self._p256_secret


    @property
    def public_key(self):
        return self._public_key


    @params(object, bytes, {bool, types.NoneType})
    def unseal(self, cipher, ignore_header=False):
        try:
            buffer = SealedDataBuffer()
            buffer.ParseFromString(cipher)

            if buffer.proof != 1:
                return FC.hybrid_unseal(self._curve25519_secret, self._p256_secret, cipher, False)

            if buffer.protocol_version == 1:
                return FC.hybrid_unseal(self._curve25519_secret, self._p256_secret, buffer.ciphertext, True)
            else:
                raise CryptoException('Unsupported SealedData protocol version {}'.format(buffer.protocol_version))

        except ProtobufErrors:
            return FC.hybrid_unseal(self._curve25519_secret, self._p256_secret, cipher, False)


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
            key=self.key
        )


    def serialize(self):
        b64_enc_private_key = b64enc(self.buffer.SerializeToString())
        return b64_enc_private_key
