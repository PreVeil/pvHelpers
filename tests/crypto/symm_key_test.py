import base64
import os
import random

from pvHelpers import SYMM_KEY_PROTOCOL_VERSION, PVKeyFactory
import pytest


@pytest.mark.parametrize("protocol_version", [
    SYMM_KEY_PROTOCOL_VERSION.V0,
    # SYMM_KEY_PROTOCOL_VERSION.V1
])
def test_symmetric_key(protocol_version):
    k = PVKeyFactory.newSymmKey(protocol_version=protocol_version)

    # encrypt/decrypt
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    ciphers = [k.encrypt(plaintext) for _ in range(500)]
    assert len(ciphers) == len(set(ciphers))
    for c in ciphers:
        assert plaintext == k.decrypt(c)

    k2 = PVKeyFactory.newSymmKey(
        protocol_version=protocol_version, secret=k._secret)
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert plaintext == k.decrypt(k2.encrypt(plaintext))
    assert plaintext == k2.decrypt(k.encrypt(plaintext))
    assert k == k2
    assert k.serialize() == k2.serialize()
