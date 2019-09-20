import base64
import os
import random

import pytest

from pvHelpers.crypto import SIGN_KEY_PROTOCOL_VERSION, PVKeyFactory


@pytest.mark.parametrize("protocol_version", [
    SIGN_KEY_PROTOCOL_VERSION.V0,
    SIGN_KEY_PROTOCOL_VERSION.V1,
    SIGN_KEY_PROTOCOL_VERSION.V3
])
def test_signing_key_v3(protocol_version):
    k = PVKeyFactory.newSignKey(protocol_version=protocol_version)

    # sign/verify
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))

    signatures = [k.sign(plaintext) for _ in range(500)]

    # NOTE: this is due to a bug in V0/V1 `protocol_version`s
    if protocol_version == SIGN_KEY_PROTOCOL_VERSION.V3:
        assert len(signatures) == len(set(signatures))

    for s in signatures:
        assert k.verify_key.verify(plaintext, s)
        assert k.verify_key.verify(
            plaintext, s[:21] + "a" + s[22:]) is False

    k2 = PVKeyFactory.newSignKey(
        protocol_version=protocol_version, key=k.key)
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert k2.verify_key.verify(plaintext, k.sign(plaintext))
    assert k.verify_key.verify(plaintext, k2.sign(plaintext))
    assert k == k2
    assert k.serialize() == k2.serialize()
