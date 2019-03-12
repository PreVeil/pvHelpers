import types
import fipscrypto as FC
from .symm_key_base import SymmKeyBase
from ..utils import params, RandomBytes, KeyBuffer, utf8Encode, b64enc, CryptoException, utf8Decode, b64dec, jdumps, \
    HexEncode, Sha256Sum, jloads


class SymmKeyV1(SymmKeyBase):
    protocol_version = 1


    @params(object, {bytes, types.NoneType})
    def __init__(self, secret=None):
        super(SymmKeyV1, self).__init__(self.protocol_version)
        if secret and len(secret) != FC.AES_KEY_LENGTH:
            raise CryptoException("Invalid aes key length")

        self._secret = secret or RandomBytes(length=FC.AES_KEY_LENGTH)


    @property
    def secret(self):
        return self._secret


    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self._secret
        )


    def serialize(self):
        return self.buffer.SerializeToString()


    @params(object, bytes, {dict, types.NoneType})
    def encrypt(self, message, details=None):
        cipher, tag, iv = FC.aes_encrypt(self._secret, message)
        cipher = cipher + iv + tag

        if details != None:
            details["sha256"] = HexEncode(Sha256Sum(cipher))
            details["length"] = len(cipher)

        return cipher


    @params(object, bytes)
    def decrypt(self, cipher):
        tag = cipher[-(FC.AES_TAG_LENGTH):]
        iv = cipher[-(FC.AES_TAG_LENGTH + FC.IV_LENGTH):-(FC.AES_TAG_LENGTH)]
        raw_cipher = cipher[:-(FC.AES_TAG_LENGTH + FC.IV_LENGTH)]

        return FC.aes_decrypt(self._secret, raw_cipher, tag, iv)


    def __eq__(self, other):
        return self.protocol_version == other.protocol_version and \
            self._secret == other._secret


    def __ne__(self, other):
        return not self.__eq__(other)
