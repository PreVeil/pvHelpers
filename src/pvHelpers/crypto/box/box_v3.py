import struct

import fipscrypto as FC
import libnacl

from pvHelpers.crypto.asymm_key import (AsymmKeyBase, AsymmKeyV3,
                                        PublicKeyBase, PublicKeyV3)
from pvHelpers.crypto.header_bytes import (ASYMM_BIT, BINARY_BIT,
                                           HEADER_LENGTH, TEXT_BIT)
from pvHelpers.utils import WrapExceptions, params


class AsymmBoxV3(object):

    @staticmethod
    @params(AsymmKeyV3, PublicKeyV3)
    def get_shared_key(private_key, public_key):
        return FC.get_ecdh_shared_key(
            (private_key._curve25519_secret, private_key._p256_secret),
            (public_key.curve25519_pub, public_key.p256_pub))


    @staticmethod
    @params(AsymmKeyV3, PublicKeyV3, bytes)
    def encrypt(private_key, public_key, plaintext):
        return FC.hybrid_box_encrypt(
            (private_key._curve25519_secret, private_key._p256_secret),
            (public_key.curve25519_pub, public_key.p256_pub),
            plaintext)


    @staticmethod
    @params(AsymmKeyV3, PublicKeyV3, bytes)
    def decrypt(private_key, public_key, ciphertext):
        return FC.hybrid_box_decrypt(
            (private_key._curve25519_secret, private_key._p256_secret),
            (public_key.curve25519_pub, public_key.p256_pub),
            ciphertext)
