from .asymm_key_base import *
from ..utils import CryptoException, b64enc, params

class AsymmKeyV1(AsymmKeyBase):
    protocol_version = 1

    @params(object, int, bytes, bytes)
    def __init__(self, key_version, enc_seed, sign_seed):
        if len(enc_seed) != libnacl.crypto_box_SECRETKEYBYTES:
            raise ValueError("enc_seed must be {} bytes long".format(libnacl.crypto_box_SECRETKEYBYTES))
        if len(sign_seed) != libnacl.crypto_sign_SEEDBYTES:
            raise ValueError("sign_seed must be {} bytes long".format(libnacl.crypto_sign_SEEDBYTES))

        self._private_key = libnacl.public.SecretKey(Sha512Sum(enc_seed)[:libnacl.crypto_box_SECRETKEYBYTES])
        self._signing_key = libnacl.sign.Signer(sign_seed)
        self._enc_seed = enc_seed
        self._sign_seed = sign_seed
        super(AsymmKeyV1, self).__init__(self.protocol_version, key_version)

    def getPublicKey(self):
        return PublicKeyV2()

    @params(object, unicode)
    def signText(self, message):
        status, raw_message = utf8Encode(message)
        if not status:
            raise RuntimeError("Failed to utf8 encode")

        status, b46_signed_message = b64enc(self._signing_key.signature(raw_message))
        if not status:
            raise RuntimeError("Failed to b64 encode")

        return b46_signed_message

    @params(object, bytes)
    def signBinary(self, message):
        status, b46_signed_message = b64enc(self._signing_key.signature(message))
        if not status:
            raise RuntimeError("Failed to b64 encode")

        return b46_signed_message

    @params(object, unicode)
    def unsealText(self, cipher):
        status, ciphertext = b64dec(cipher)
        if not status:
            raise RuntimeError("Failed to b64 decode")

        raw_message = self._private_key.seal_open(cipher)
        status, message = utf8Decode(raw_message)
        if not status:
            raise RuntimeError("Failed to utf8 decode")

        return message

    @params(object, unicode)
    def unsealBinary(self, cipher):
        status, ciphertext = b64dec(cipher)
        if not status:
            raise RuntimeError("Failed to b64 decode")

        message = self._private_key.seal_open(cipher)
        return message

    def _serializeEncKey(self):
        status, b64_encoded_key = b64enc(self._enc_seed)
        if status == False:
            raise RuntimeError("Failed to b64 encode the secret")
        return b64_encoded_key

    def _serializeSignKey(self):
        status, b64_encoded_key = b64enc(self._sign_seed)
        if status == False:
            raise RuntimeError("Failed to b64 encode the signing seed")
        return b64_encoded_key



class PublicKeyV1(PublicKeyBase):
    protocol_version = 0

    @params(object, bytes)
    def __init__(self, public_key):
        super(PublicKeyV0, self).__init__(self.protocol_version)
        self._public_key = libnacl.public.PublicKey(public_key)

    @params(object, {str, bytes})
    def seal(self, message):
        message_with_header = struct.pack(">BBBB", BINARY_BIT | SEAL_BIT, 0x00, 0x00, 0x00) + message
        try:
            return self._public_key.seal(message_with_header)
        except (libnacl.CryptError, ValueError) as e:
            raise CryptoException(e)

    def serialize(self):
        status, b64_enc_public_key = b64enc(self._public_key.pk)
        if status == False:
            raise CryptoException(RuntimeError("Failed to b46 enc public key"))
        return b64_enc_public_key


    # def verifyText(self, message, signature):
    #     raise NotImplementedError("verifyText must be implemented by children")
    #
    # def verifyBinary(self, message, signature):
    #     raise NotImplementedError("verifyBinary must be implemented by children")

    # @params(object, unicode)
    # def sealText(self, message):
    #     status, raw_message = utf8Encode(message)
    #     if not status:
    #         raise RuntimeError("Failed to utf8 encode")
    #     status, b46_chiper = b64enc(self._seal(raw_message))
    #     if not status:
    #         raise RuntimeError("Failed to b64 encode")
    #
    #     return b46_chiper
    #
    # @params(object, {str, bytes})
    # def sealBinary(self, message):
    #     status, b46_chiper = b64enc(self._seal(message))
    #     if not status:
    #         raise RuntimeError("Failed to b64 encode")
    #
    #     return b46_chiper
