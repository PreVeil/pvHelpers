import os
import base64
import random

from pvHelpers import PVKeyFactory, ASYMM_KEY_PROTOCOL_VERSION

def xtest_encryption_key_v3():
    k = PVKeyFactory.newAsymmKey(protocol_version=ASYMM_KEY_PROTOCOL_VERSION.V3)

    # seal/unseal
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert plaintext == k.unseal(k.public_key.seal(plaintext))

    # plaintext = unicode(
    #     base64.encodestring(os.urandom(1024 * 2 + random.randint(0, 1024))))
    # assert plaintext == k.unsealText(k.public_key.sealText(plaintext))

    k2 = PVKeyFactory.newAsymmKey(
        protocol_version=ASYMM_KEY_PROTOCOL_VERSION.V3, key=k.key)
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert plaintext == k.unseal(k2.public_key.seal(plaintext))
    assert plaintext == k2.unseal(k.public_key.seal(plaintext))

    assert k == k2
    assert k.serialize() == k2.serialize()
