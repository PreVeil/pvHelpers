import struct
import types

import libnacl
from pvHelpers.crypto.header_bytes import (BINARY_BIT, HEADER_LENGTH,
                                           SECRET_BIT, TEXT_BIT)
from pvHelpers.crypto.utils import CryptoException, hex_encode, sha_256_sum
from pvHelpers.utils import (b64dec, b64enc, EncodingException, jdumps, jloads,
                             params, utf8_decode, utf8_encode, WrapExceptions)

from .base import SymmKeyBase


class SymmKeyV0(SymmKeyBase):
    protocol_version = 0

    @params(object, {bytes, types.NoneType})
    def __init__(self, secret=None):
        super(SymmKeyV0, self).__init__(self.protocol_version)
        self._box = libnacl.secret.SecretBox(secret)
        self._secret = self._box.sk

    @property
    def secret(self):
        return self._box.sk

    def serialize(self):
        b64 = b64enc(self._box.sk)
        return utf8_encode(b64enc(utf8_encode(jdumps({
            "material": b64
        }))))

    @classmethod
    @WrapExceptions(CryptoException, [EncodingException])
    @params(object, bytes)
    def deserialize(cls, key):
        key = jloads(utf8_decode(b64dec(utf8_decode(key))))

        key = key.get("material")
        if not key:
            raise CryptoException("Missing material")
        secret = b64dec(key)
        return cls(secret)

    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes, {dict, types.NoneType},  bool)
    def encrypt(self, message, details=None, is_text=False):
        if is_text:
            message_with_header = struct.pack(">BBBB", TEXT_BIT | SECRET_BIT, 0x00, 0x00, 0x00) + message
        else:
            message_with_header = struct.pack(">BBBB", BINARY_BIT | SECRET_BIT, 0x00, 0x00, 0x00) + message

        cipher = self._box.encrypt(message_with_header)
        if details is not None:
            details["sha256"] = hex_encode(sha_256_sum(cipher))
            details["length"] = len(cipher)

        return cipher

    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes)
    def decrypt(self, cipher):
        message = self._box.decrypt(cipher)
        return message[HEADER_LENGTH:]

    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._secret == other._secret

    def __ne__(self, other):
        return not self.__eq__(other)
