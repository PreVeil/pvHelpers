import struct, types, libnacl, libnacl.public
from .asymm_key_base import *
from ..utils import CryptoException, b64dec, b64enc, params, g_log, utf8Encode, utf8Decode

# The first four bytes of encrypted data are reservered for internal use. When
# packing our bits with the struct module, make sure to pick a byte order (eg, >)
# otherwise python will choose native ordering and it might do something weird
# with alignment.
# The most sig bit of the first byte is the 'text' bit.
BINARY_BIT = 0x00
TEXT_BIT = 0x80
# The next three bits indicate encryption 'type'
ASYMM_BIT = 0x00
SEAL_BIT = 0x10
SECRET_BIT = 0x20

class PublicKeyV0(PublicKeyBase):
    protocol_version = 0

    @params(object, bytes)
    def __init__(self, public_key):
        super(PublicKeyV0, self).__init__(self.protocol_version)
        self._public_key = libnacl.public.PublicKey(public_key)

    @property
    def pk(self):
        return self._public_key.pk

    @params(object, bytes)
    def sealBinary(self, message):
        message_with_header = struct.pack(">BBBB", BINARY_BIT | SEAL_BIT, 0x00, 0x00, 0x00) + message
        try:
            sealed_message = self._public_key.seal(message_with_header)
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


class AsymmKeyV0(AsymmKeyBase):
    protocol_version = 0
    public_side_model = PublicKeyV0

    @params(object, {bytes, types.NoneType})
    def __init__(self, enc_secret=None):
        super(AsymmKeyV0, self).__init__(self.protocol_version)
        self._key_pair = libnacl.public.SecretKey(enc_secret)
        self._public_key = self.public_side_model(self._key_pair.pk)

    @property
    def sk(self):
        return self._key_pair.sk

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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._key_pair.sk == other.sk
