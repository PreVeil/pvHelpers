import struct
import types

import libnacl
import libnacl.public
from pvHelpers.crypto.header_bytes import (BINARY_BIT, HEADER_LENGTH,
                                           SEAL_BIT, TEXT_BIT)
from pvHelpers.crypto.utils import CryptoException
from pvHelpers.utils import b64enc, params, WrapExceptions

from .base import AsymmKeyBase, PublicKeyBase


class PublicKeyV0(PublicKeyBase):
    protocol_version = 0

    @params(object, bytes)
    def __init__(self, public_key):
        super(PublicKeyV0, self).__init__(self.protocol_version)
        self._public_key = libnacl.public.PublicKey(public_key)

    @property
    def key(self):
        return self._public_key.pk

    @property
    def pk(self):
        return self._public_key.pk

    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes, bool)
    def seal(self, message, is_text=False):
        if is_text:
            message_with_header = struct.pack(">BBBB", TEXT_BIT | SEAL_BIT, 0x00, 0x00, 0x00) + message
        else:
            message_with_header = struct.pack(">BBBB", BINARY_BIT | SEAL_BIT, 0x00, 0x00, 0x00) + message
        return self._public_key.seal(message_with_header)


class AsymmKeyV0(AsymmKeyBase):
    protocol_version = 0
    public_side_model = PublicKeyV0

    @params(object, {bytes, types.NoneType})
    def __init__(self, key=None):
        super(AsymmKeyV0, self).__init__(self.protocol_version)
        self._key_pair = libnacl.public.SecretKey(key)
        self._public_key = self.public_side_model(self._key_pair.pk)

    @property
    def key(self):
        return self._key_pair.sk

    @property
    def sk(self):
        return self._key_pair.sk

    @property
    def public_key(self):
        return self._public_key

    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes)
    def unseal(self, cipher):
        message_with_header = self._key_pair.seal_open(cipher)
        return message_with_header[HEADER_LENGTH:]

    def serialize(self):
        b64_enc_private_key = b64enc(self._key_pair.sk)
        return b64_enc_private_key

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        return self._key_pair.sk == other.sk
