import types, libnacl, libnacl.sign
from .sign_key_base import *
from ..utils import CryptoException, b64enc, params, HexEncode, utf8Encode, b64dec

class SignKeyV0(SignKeyBase):
    protocol_version = 0

    @params(object, {bytes, types.NoneType})
    def __init__(self, seed=None):
        super(SignKeyV0, self).__init__(self.protocol_version)
        self._signer = libnacl.sign.Signer(seed)
        self._verify_key = VerifyKeyV0(self._signer.vk)

    @property
    def verify_key(self):
        return self._verify_key

    def serialize(self):
        status, b64_enc_signing_seed = b64enc(self._signer.seed)
        if status == False:
            raise CryptoException("Failed to b46 enc signing seed")
        return b64_enc_signing_seed

    @params(object, unicode)
    def signText(self, message):
        status, raw_message = utf8Encode(message)
        if not status:
            raise CryptoException("Failed to utf8 encode message")

        return self.signBinary(raw_message)

    @params(object, bytes)
    def signBinary(self, message):
        status, b64_signature = b64enc(self._signer.signature(message))
        if not status:
            raise CryptoException("Failed to b64 encode signature")
        return b64_signature

class VerifyKeyV0(VerifyKeyBase):
    protocol_version = 0

    @params(object, bytes)
    def __init__(self, verifier_key):
        super(VerifyKeyV0, self).__init__(self.protocol_version)
        self._verifier = libnacl.sign.Verifier(HexEncode(verifier_key))

    @params(object, unicode, unicode)
    def verifyText(self, message, signature):
        status, raw_message = utf8Encode(message)
        if not status:
            raise CryptoException("Failed to utf8 encode message")
        return self.verifyBinary(raw_message, signature)

    @params(object, bytes, unicode)
    def verifyBinary(self, message, signature):
        status, signature = b64dec(signature)
        if not status:
            raise CryptoException("Failed to b64 decode signature")

        try:
            self._verifier.verify(signature + message)
        except ValueError as e:
            return False
        except libnacl.CryptError as e:
            raise CryptoException(e)
        return True

    def serialize(self):
        status, b64_enc_verify_key = b64enc(self._verifier.vk)
        if status == False:
            raise CryptoException("Failed to b46 enc verify key")
        return b64_enc_verify_key