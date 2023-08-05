from __future__ import absolute_import
import struct, libnacl
from ..asymm_key import AsymmKeyBase, PublicKeyBase, AsymmKeyV3, PublicKeyV3
from pvHelpers.hook_decorators import WrapExceptions
from ..utils import CryptoException, utf8Encode, utf8Decode, b64enc, b64dec, HexEncode, Sha512Sum, params
from ..header_bytes import ASYMM_BIT, BINARY_BIT, TEXT_BIT, HEADER_LENGTH
import fipscrypto as FC

class AsymmBoxV3(object):

    @staticmethod
    @params(AsymmKeyV3, PublicKeyV3, bool)
    def get_shared_key(private_key, public_key, use_fips_derivation):
        return FC.get_ecdh_shared_key(
            (private_key._curve25519_secret, private_key._p256_secret),
            (public_key.curve25519_pub, public_key.p256_pub),
            use_fips_derivation)


    @staticmethod
    @params(AsymmKeyV3, PublicKeyV3, bytes, bool)
    def encrypt(private_key, public_key, plaintext, use_fips_derivation):
        return FC.hybrid_box_encrypt(
            (private_key._curve25519_secret, private_key._p256_secret),
            (public_key.curve25519_pub, public_key.p256_pub),
            plaintext,
            use_fips_derivation)


    @staticmethod
    @params(AsymmKeyV3, PublicKeyV3, bytes, bool)
    def decrypt(private_key, public_key, ciphertext, use_fips_derivation):
        return FC.hybrid_box_decrypt(
             (private_key._curve25519_secret, private_key._p256_secret),
             (public_key.curve25519_pub, public_key.p256_pub),
            ciphertext,
            use_fips_derivation)