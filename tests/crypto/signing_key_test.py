import base64
import os
import random

from pvHelpers import SIGN_KEY_PROTOCOL_VERSION, PVKeyFactory


def xtest_signing_key_v3():
    k = PVKeyFactory.newSignKey(protocol_version=SIGN_KEY_PROTOCOL_VERSION.V3)

    # sign/verify
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))

    signatures = [k.sign(plaintext) for _ in range(500)]
    assert len(signatures) == len(set(signatures))
    for s in signatures:
        assert k.verify_key.verify(plaintext, s)
        assert k.verify_key.verify(
            plaintext, s[:21] + "a" + s[22:]) is False

    k2 = PVKeyFactory.newSignKey(
        protocol_version=SIGN_KEY_PROTOCOL_VERSION.V3, key=k.key)
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert k2.verify_key.verify(plaintext, k.sign(plaintext))
    assert k.verify_key.verify(plaintext, k2.sign(plaintext))
    assert k == k2
    assert k.serialize() == k2.serialize()
