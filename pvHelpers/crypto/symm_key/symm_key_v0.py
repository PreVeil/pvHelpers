import types, libnacl, struct
from .symm_key_base import *
from ..utils import params, utf8Encode, b64enc, CryptoException, utf8Decode, b64dec, jdumps, HexEncode, Sha256Sum, jloads
from ..header_bytes import TEXT_BIT, SECRET_BIT, BINARY_BIT, HEADER_LENGTH

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
        status, b64 = b64enc(self._box.sk)
        if not status:
            raise CryptoException("failed to b64 encode secret")
        status, raw_key = utf8Encode(jdumps({
            "material": b64
        }))
        if not status:
            raise CryptoException("Failed to utf8 encode")
        status, b64_key = b64enc(raw_key)
        if not status:
            raise CryptoException("Failed to b64 encode")
        return b64_key


    @classmethod
    @params(object, {"key": bytes})
    def fromDict(cls, key_dict):
        status, key = utf8Decode(key_dict["key"])
        if not status:
            raise CryptoException("Failed to utf8 decode key")
        status, key = jloads(key)
        if not status:
            raise CryptoException("Failed to deserialize key")
        key = key.get("material")
        if not key:
            raise CryptoException("Missing material")
        status, secret = b64dec(key)
        if not status:
            raise CryptoException("Failed to b64 decode material")
        return cls(secret)

    @params(object, unicode, {dict, types.NoneType})
    def encryptText(self, message, details=None):
        status, raw_message = utf8Encode(message)
        if not status:
            raise CryptoException("Failed to utf8 encode message")
        message_with_header = struct.pack(">BBBB", TEXT_BIT | SECRET_BIT, 0x00, 0x00, 0x00) + raw_message
        try:
            cipher = self._box.encrypt(message_with_header)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)
        if details != None:
            details["sha256"] = HexEncode(Sha256Sum(cipher))
            details["length"] = len(cipher)
        status, b64_cipher = b64enc(cipher)
        if not status:
            raise CryptoException("Failed to b64 encode cipher")
        return b64_cipher

    @params(object, unicode)
    def decryptText(self, cipher):
        status, raw_cipher = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")
        try:
            message_with_header = self._box.decrypt(raw_cipher)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)
        header = struct.unpack(">BBBB", message_with_header[:HEADER_LENGTH])
        if header[0] != (TEXT_BIT | SECRET_BIT):
            raise CryptoException("Invalid header byte {}".format(header))

        status, message = utf8Decode(message_with_header[HEADER_LENGTH:])
        if not status:
            raise CryptoException("Failed to utf8 message")

        return message

    @params(object, bytes, {dict, types.NoneType})
    def encryptBinary(self, message, details=None):
        message_with_header = struct.pack(">BBBB", BINARY_BIT | SECRET_BIT, 0x00, 0x00, 0x00) + message
        try:
            cipher = self._box.encrypt(message_with_header)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)
        if details != None:
            details["sha256"] = HexEncode(Sha256Sum(cipher))
            details["length"] = len(cipher)
        status, b64_cipher = b64enc(cipher)
        if not status:
            raise CryptoException("Failed to b64 encode cipher")

        return b64_cipher

    @params(object, unicode)
    def decryptBinary(self, cipher):
        status, raw_cipher = b64dec(cipher)
        if not status:
            raise CryptoException("Failed to b64 decode cipher")
        try:
            message = self._box.decrypt(raw_cipher)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)
        header_byte = struct.unpack(">BBBB", message[:HEADER_LENGTH])[0]
        if header_byte != (BINARY_BIT | SECRET_BIT):
            raise CryptoException("Invalid header byte {}".format(header_byte))

        return message[HEADER_LENGTH:]

    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._secret == other._secret

    def __ne__(self, other):
        return not self.__eq__(other)
