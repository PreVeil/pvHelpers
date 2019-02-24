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

    # @params(object, unicode)
    # def XencryptText(self, message):
    #     status, raw_message = utf8Encode(message)
    #     if not status:
    #         raise CryptoException("Failed to utf8 encode message")
    #
    #     header = struct.pack(">BBBB", TEXT_BIT | ASYMM_BIT, 0x00, 0x00, 0x00)
    #     try:
    #         cipher = self.__box.encrypt(header + raw_message)
    #     except (libnacl.CryptError, ValueError) as e:
    #         raise CryptoException(e)
    #
    #     status, b64 = b64enc(cipher)
    #     if not status:
    #         raise CryptoException("Failed to b64 encode cipher")
    #     return b64

    # @params(object, unicode)
    # def XdecryptText(self, cipher):
    #     status, decoded_ciphertext = b64dec(cipher)
    #     if not status:
    #         raise CryptoException("Failed to b64 decode cipher")
    #
    #     try:
    #         message_with_header = self.__box.decrypt(decoded_ciphertext)
    #     except (libnacl.CryptError, ValueError) as e:
    #         raise CryptoException(e)
    #
    #     header = struct.unpack(">BBBB", message_with_header[:HEADER_LENGTH])
    #     if header[0] != (TEXT_BIT | ASYMM_BIT):
    #         raise CryptoException("Invalid header byte {}".format(header))
    #
    #     status, message = utf8Decode(message_with_header[HEADER_LENGTH:])
    #     if not status:
    #         raise CryptoException("Failed to utf8 decode message")
    #     return message

    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes)
    def encrypt(self, message):
        message_with_header = struct.pack(">BBBB", BINARY_BIT | ASYMM_BIT, 0x00, 0x00, 0x00) + message

        # status, b64 = b64enc(cipher)
        # if not status:
        #     raise CryptoException("Failed to b64 encode cipher")
        return self.__box.encrypt(message_with_header)

    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes)
    def decrypt(self, cipher):
        # status, decoded_ciphertext = b64dec(cipher)
        # if not status:
        #     raise CryptoException("Failed to b64 decode cipher")

        message_with_header = self.__box.decrypt(decoded_ciphertext)

        # header = struct.unpack(">BBBB", message_with_header[:HEADER_LENGTH])
        # if header[0] != (BINARY_BIT | ASYMM_BIT):
        #     raise CryptoException("Invalid header byte {}".format(header))

        return message_with_header[HEADER_LENGTH:]

    def getPin(self):
        secret = self.__box._k
        secret_hash = HexEncode(Sha512Sum(secret))
        return secret_hash[:8]
