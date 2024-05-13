import struct, libnacl
from ..asymm_key import AsymmKeyBase, PublicKeyBase
from pvHelpers.hook_decorators import WrapExceptions
from ..utils import CryptoException, utf8Encode, utf8Decode, b64enc, b64dec, HexEncode, Sha512Sum, params
from ..header_bytes import ASYMM_BIT, BINARY_BIT, TEXT_BIT, HEADER_LENGTH


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
    def decrypt(self, cipher, ignore_header=False):
        message_with_header = self.__box.decrypt(cipher)
        return message_with_header if ignore_header else message_with_header[HEADER_LENGTH:]


    def getPin(self):
        secret = self.__box._k
        secret_hash = HexEncode(Sha512Sum(secret))
        return secret_hash[:8]
