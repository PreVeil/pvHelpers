import struct

import libnacl
from pvHelpers.crypto.asymm_key import AsymmKeyBase, PublicKeyBase
from pvHelpers.crypto.header_bytes import (ASYMM_BIT, BINARY_BIT,
                                           HEADER_LENGTH, TEXT_BIT)
from pvHelpers.crypto.utils import CryptoException, hex_encode, sha_512_sum
from pvHelpers.utils import params, WrapExceptions


class AsymmBox(object):

    @params(object, AsymmKeyBase, PublicKeyBase)
    def __init__(self, private_key, public_key):
        self.__private_key = private_key
        self.__public_key = public_key
        self.__box = libnacl.public.Box(self.__private_key._key_pair, self.__public_key._public_key)

    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes, bool)
    def encrypt(self, message, is_text=False):
        if is_text:
            message_with_header = struct.pack(">BBBB", TEXT_BIT | ASYMM_BIT, 0x00, 0x00, 0x00) + message
        else:
            message_with_header = struct.pack(">BBBB", BINARY_BIT | ASYMM_BIT, 0x00, 0x00, 0x00) + message
        return self.__box.encrypt(message_with_header)

    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes)
    def decrypt(self, cipher):
        message_with_header = self.__box.decrypt(cipher)
        return message_with_header[HEADER_LENGTH:]

    def get_pin(self):
        secret = self.__box._k
        secret_hash = hex_encode(sha_512_sum(secret))
        return secret_hash[:8]
