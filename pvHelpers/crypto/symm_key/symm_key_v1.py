import types, struct

import fipscrypto as FC

from .symm_key_base import SymmKeyBase
from ..header_bytes import BINARY_BIT, TEXT_BIT, SECRET_BIT, HEADER_LENGTH
from ..utils import params, RandomBytes, KeyBuffer, utf8Encode, b64enc, CryptoException, utf8Decode, b64dec, jdumps, HexEncode, Sha256Sum, jloads

class SymmKeyV1(SymmKeyBase):
    protocol_version = 1

    @params(object, {bytes, types.NoneType})
    def __init__(self, secret=None):
        super(SymmKeyV1, self).__init__(self.protocol_version)
        if secret and len(secret) != FC.AES_KEY_LENGTH:
            raise CryptoException("Invalid aes key length")

        self._secret = secret or RandomBytes(length=FC.AES_KEY_LENGTH)

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self._secret
        )

    def serialize(self):
        return self.buffer.SerializeToString()


    @params(object, unicode)
    def encryptText(self, message):
        status, raw_message = utf8Encode(message)
        if not status:
            raise CryptoException("Failed to utf8 encode message")
        message_with_header = struct.pack(">BBBB", TEXT_BIT | SECRET_BIT, 0x00, 0x00, 0x00) + raw_message
        cipher, tag, iv = FC.aes_encrypt(self._secret, message_with_header)
        cipher = cipher + iv + tag

        status, b64_cipher = b64enc(cipher)
        if not status:
            raise CryptoException("Failed to b64 encode cipher")
        return b64_cipher


    @params(object, unicode)
    def decryptText(self, cipher):
        status, raw_cipher = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")

        tag = raw_cipher[-(FC.AES_TAG_LENGTH):]
        iv = raw_cipher[-(FC.AES_TAG_LENGTH + FC.IV_LENGTH):-(FC.AES_TAG_LENGTH)]
        cipher = raw_cipher[:-(FC.AES_TAG_LENGTH + FC.IV_LENGTH)]

        message_with_header = FC.aes_decrypt(self._secret, cipher, tag, iv)
        header = struct.unpack(">BBBB", message_with_header[:HEADER_LENGTH])
        if header[0] != (TEXT_BIT | SECRET_BIT):
            raise CryptoException("Invalid header byte {}".format(header))

        status, message = utf8Decode(message_with_header[HEADER_LENGTH:])
        if not status:
            raise CryptoException("Failed to utf8 message")

        return message


    @params(object, bytes)
    def encryptBinary(self, message):
        message_with_header = struct.pack(">BBBB", BINARY_BIT | SECRET_BIT, 0x00, 0x00, 0x00) + message

        cipher, tag, iv = FC.aes_encrypt(self._secret, message_with_header)
        cipher = cipher + iv + tag

        status, b64_cipher = b64enc(cipher)
        if not status:
            raise CryptoException("Failed to b64 encode cipher")

        return b64_cipher


    @params(object, unicode)
    def decryptBinary(self, cipher):
        status, raw_cipher = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")

        tag = raw_cipher[-(FC.AES_TAG_LENGTH):]
        iv = raw_cipher[-(FC.AES_TAG_LENGTH + FC.IV_LENGTH):-(FC.AES_TAG_LENGTH)]
        cipher = raw_cipher[:-(FC.AES_TAG_LENGTH + FC.IV_LENGTH)]

        message_with_header = FC.aes_decrypt(self._secret, cipher, tag, iv)
        header_byte = struct.unpack(">BBBB", message_with_header[:HEADER_LENGTH])[0]
        if header_byte != (BINARY_BIT | SECRET_BIT):
            raise CryptoException("Invalid header byte {}".format(header_byte))

        return message_with_header[HEADER_LENGTH:]


    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._secret == other._secret


    def __ne__(self, other):
        return not self.__eq__(other)
