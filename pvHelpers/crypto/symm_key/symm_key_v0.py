import types, libnacl, struct
from .symm_key_base import *
from pvHelpers.hook_decorators import WrapExceptions
from ..utils import params, utf8Encode, b64enc, CryptoException, utf8Decode, b64dec, jdumps, HexEncode, Sha256Sum, jloads
from ..header_bytes import TEXT_BIT, SECRET_BIT, BINARY_BIT, HEADER_LENGTH
from pvHelpers import EncodingException

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
        return utf8Encode(b64enc(utf8Encode(jdumps({
            "material": b64
        }))))


    @classmethod
    @WrapExceptions(CryptoException, [EncodingException])
    @params(object, bytes)
    def deserialize(cls, key):
        key = jloads(utf8Decode(b64dec(utf8Decode(key))))

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
        if details != None:
            details["sha256"] = HexEncode(Sha256Sum(cipher))
            details["length"] = len(cipher)

        return cipher


    @WrapExceptions(CryptoException, [libnacl.CryptError, ValueError])
    @params(object, bytes)
    def decrypt(self, cipher, ignore_header=False):
        message = self._box.decrypt(cipher)
        header_byte = struct.unpack(">BBBB", message[:HEADER_LENGTH])[0]
        return message if ignore_header else message[HEADER_LENGTH:]


    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._secret == other._secret


    def __ne__(self, other):
        return not self.__eq__(other)
