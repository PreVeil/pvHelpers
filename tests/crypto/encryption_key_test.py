import os
import base64
import random

from pvHelpers import PVKeyFactory, ASYMM_KEY_PROTOCOL_VERSION

def test_encryption_key_v3():
    k = PVKeyFactory.newAsymmKey(protocol_version=ASYMM_KEY_PROTOCOL_VERSION.V3)

    # seal/unseal
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert plaintext == k.unsealBinary(k.public_key.sealBinary(plaintext))

    plaintext = unicode(
        base64.encodestring(os.urandom(1024 * 2 + random.randint(0, 1024))))
    assert plaintext == k.unsealText(k.public_key.sealText(plaintext))

    k2 = PVKeyFactory.newAsymmKey(
        protocol_version=ASYMM_KEY_PROTOCOL_VERSION.V3, key=k.key)
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert plaintext == k.unsealBinary(k2.public_key.sealBinary(plaintext))
    assert plaintext == k2.unsealBinary(k.public_key.sealBinary(plaintext))

    assert k == k2
    assert k.serialize() == k2.serialize()
