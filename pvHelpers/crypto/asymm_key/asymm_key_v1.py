import types, libnacl
from .asymm_key_base import *
from ..utils import CryptoException, b64enc, params, RandomBytes

class AsymmKeyV1(AsymmKeyBase):
    protocol_version = 1

    @params(object, {bytes, types.NoneType})
    def __init__(self, enc_seed=None):
        if enc_seed is None:
            enc_seed = RandomBytes(libnacl.crypto_box_SECRETKEYBYTES)
        if len(enc_seed) != libnacl.crypto_box_SECRETKEYBYTES:
            raise ValueError("enc_seed must be {} bytes long".format(libnacl.crypto_box_SECRETKEYBYTES))

        self._key_pair = libnacl.public.SecretKey(Sha512Sum(enc_seed)[:libnacl.crypto_box_SECRETKEYBYTES])
        self._public_key = PublicKeyV1(self._key_pair.pk)
        self._enc_seed = enc_seed
        super(AsymmKeyV1, self).__init__(self.protocol_version)

    @property
    def public_key(self):
        return self._public_key

    @params(object, unicode)
    def unsealBinary(self, cipher):
        status, cipher = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")
        try:
            message_with_header = self._key_pair.seal_open(cipher)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)
        header = struct.unpack(">BBBB", message_with_header[:4])
        if header[0] != (BINARY_BIT | SEAL_BIT):
            raise CryptoException(u"Invalid header bytes")
        return message_with_header[4:]

    @params(object, unicode)
    def unsealText(self, cipher):
        status, cipher = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")
        try:
            message_with_header = self._key_pair.seal_open(cipher)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)
        header = struct.unpack(">BBBB", message_with_header[:4])
        if header[0] != (TEXT_BIT | SEAL_BIT):
            raise CryptoException(u"Invalid header bytes")
        status, message = utf8Decode(message_with_header[4:])
        if not status:
            raise CryptoException(u"Failed to utf8 decode message")
        return message

    def serialize(self):
        status, b64_enc_private_key = b64enc(self._key_pair.sk)
        if status == False:
            raise CryptoException("Failed to b46 encode private key")
        return b64_enc_private_key

class PublicKeyV1(PublicKeyBase):
    protocol_version = 1

    @params(object, bytes)
    def __init__(self, public_key):
        super(PublicKeyV1, self).__init__(public_key)

    @params(object, bytes)
    def sealBinary(self, message):
        try:
            sealed_message = self._public_key.seal(message)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)
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
        try:
            sealed_message = self._public_key.seal(message_with_header)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)
        status, b64 = b64enc(sealed_message)
        if not status:
            raise CryptoException("Failed to b64 encode message")
        return b64

    def serialize(self):
        status, b64_enc_public_key = b64enc(self._public_key.pk)
        if status == False:
            raise CryptoException("Failed to b46 enc public key")
        return b64_enc_public_key
