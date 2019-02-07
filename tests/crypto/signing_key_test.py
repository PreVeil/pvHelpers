import base64
import os
import random

from pvHelpers import SIGN_KEY_PROTOCOL_VERSION, PVKeyFactory


def test_signing_key_v3():
    k = PVKeyFactory.newSignKey(protocol_version=SIGN_KEY_PROTOCOL_VERSION.V3)

    # sign/verify
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    signatures = [k.signBinary(plaintext) for _ in range(500)]
    assert len(signatures) == len(set(signatures))
    for s in signatures:
        assert k.verify_key.verifyBinary(plaintext, s)
        assert k.verify_key.verifyBinary(
            plaintext, s[:21] + u"A" + s[22:]) is False

    plaintext = unicode(base64.encodestring(os.urandom(1024 * 2 + random.randint(0, 1024))))
    signatures = [k.signText(plaintext) for _ in range(500)]
    assert len(signatures) == len(set(signatures))
    for s in signatures:
        assert k.verify_key.verifyText(plaintext, s)
        assert k.verify_key.verifyText(
            plaintext, s[:21] + u"A" + s[22:]) is False


    k2 = PVKeyFactory.newSignKey(
        protocol_version=SIGN_KEY_PROTOCOL_VERSION.V3, key=k.key)
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert k2.verify_key.verifyBinary(
        plaintext,
        k.signBinary(plaintext))
    assert k.verify_key.verifyBinary(
        plaintext,
        k2.signBinary(plaintext))
    assert k == k2
    assert k.serialize() == k2.serialize()
