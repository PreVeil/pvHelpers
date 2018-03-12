import struct
from ..asymm_key import AsymmKeyBase, PublicKeyBase
from ..utils import CryptoException, utf8Encode, utf8Decode, b64enc, b64dec, HexEncode, Sha512Sum, params

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

#TODO: add protocol_version to this module
class AsymmBox(object):
    @params(object, AsymmKeyBase, PublicKeyBase)
    def __init__(self, private_key, public_key):
        self.__private_key = private_key
        self.__public_key = public_key
        self.__box = libnacl.public.Box(self.__private_key._key_pair, self.__public_key._public_key)

    @params(object, unicode)
    def encryptText(self, message):
        status, raw_message = utf8Encode(message)
        if not status:
            raise CryptoException("Failed to utf8 encode message")

        header = struct.pack(">BBBB", TEXT_BIT | ASYMM_BIT, 0x00, 0x00, 0x00)
        try:
            cipher = self.__box.encrypt(header + raw_message)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)

        status, b64 = b64enc(cipher)
        if not status:
            raise CryptoException("Failed to b64 encode cipher")
        return b64

    @params(object, unicode)
    def decryptText(self, cipher):
        status, decoded_ciphertext = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")

        try:
            message_with_header = self.__box.decrypt(decoded_ciphertext)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)

        header = struct.unpack(">BBBB", message_with_header[:4])
        if header[0] != (TEXT_BIT | ASYMM_BIT):
            raise CryptoException("Invalid header byte {}".format(header))

        status, message = utf8Decode(message_with_header[4:])
        if not status:
            raise CryptoException("Failed to utf8 decode message")
        return message

    @params(object, bytes)
    def encryptBinary(self, message):
        message_with_header = struct.pack(">BBBB", BINARY_BIT | ASYMM_BIT, 0x00, 0x00, 0x00) + message
        try:
            cipher = self.__box.encrypt(message_with_header)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)

        status, b64 = b64enc(cipher)
        if not status:
            raise CryptoException("Failed to b64 encode cipher")
        return b64

    @params(object, unicode)
    def decryptBinary(self, cipher):
        status, decoded_ciphertext = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")

        try:
            message_with_header = self.__box.decrypt(decoded_ciphertext)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)

        header = struct.unpack(">BBBB", message_with_header[:4])
        if header[0] != (BINARY_BIT | ASYMM_BIT):
            raise CryptoException("Invalid header byte {}".format(header))

        return message_with_header[4:]

    def getPin(self):
        secret = self.__box._k
        secret_hash = HexEncode(Sha512Sum(secret))
        return secret_hash[:8]
