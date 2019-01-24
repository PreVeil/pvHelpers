import os, base64, random

from pvHelpers import USER_KEY_PROTOCOL_VERSION, ASYMM_KEY_PROTOCOL_VERSION, SYMM_KEY_PROTOCOL_VERSION, \
    SIGN_KEY_PROTOCOL_VERSION, PVKeyFactory, CryptoException, AsymmKeyV3, SignKeyV3
import pytest


@pytest.mark.parametrize('protocol_version', [
    USER_KEY_PROTOCOL_VERSION.V1
])
def test_user_key_creation(protocol_version):
    key = PVKeyFactory.newUserKey(0)
    assert key.protocol_version == USER_KEY_PROTOCOL_VERSION.Latest

    for key_version in range(0, 222):
        k = PVKeyFactory.newUserKey(key_version, protocol_version)
        k2 = PVKeyFactory.newUserKey(
            key_version, k.protocol_version, k.encryption_key, k.signing_key)
        assert k == k2
        assert k.key_version == key_version
        assert k.protocol_version == protocol_version
        assert k.encryption_key.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.Latest
        assert k.signing_key.protocol_version == SIGN_KEY_PROTOCOL_VERSION.Latest
        assert k2.serialize() == k.serialize()
        assert k == PVKeyFactory.deserializeUserKey(k.serialize())

    # unknown protocol_version
    with pytest.raises(CryptoException) as ex:
        PVKeyFactory.newUserKey(0, protocol_version=9999)

@pytest.mark.parametrize('protocol_version', [
    ASYMM_KEY_PROTOCOL_VERSION.V0,
    ASYMM_KEY_PROTOCOL_VERSION.V1,
    ASYMM_KEY_PROTOCOL_VERSION.V2,
    ASYMM_KEY_PROTOCOL_VERSION.V3,
])
def test_encryption_key_creation(protocol_version):
    k = PVKeyFactory.newAsymmKey(protocol_version)
    assert k.protocol_version == protocol_version


@pytest.mark.parametrize('protocol_version', [
    SIGN_KEY_PROTOCOL_VERSION.V0,
    SIGN_KEY_PROTOCOL_VERSION.V1,
    ASYMM_KEY_PROTOCOL_VERSION.V3,
])
def test_sign_key_creation(protocol_version):
    k = PVKeyFactory.newAsymmKey(protocol_version)
    assert k.protocol_version == protocol_version


def test_encryption_key_v3():
    k = AsymmKeyV3()

    # seal/unseal
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert plaintext == k.unsealBinary(k.public_key.sealBinary(plaintext))

    plaintext = unicode(base64.encodestring(os.urandom(1024 * 2 + random.randint(0, 1024))))
    assert plaintext == k.unsealText(k.public_key.sealText(plaintext))

    k2 = AsymmKeyV3(k._curve25519_secret, k._p256_secret)
    plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
    assert plaintext == k.unsealBinary(k2.public_key.sealBinary(plaintext))
    assert plaintext == k2.unsealBinary(k.public_key.sealBinary(plaintext))

    assert k == k2
    assert k.serialize() == k2.serialize()

# def test_signing_key_v3():
#     k = SignKeyV3()
#
#     # sign/verify
#     plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
#     signature = k.sign
#     assert plaintext == k.unsealBinary(k.public_key.sealBinary(plaintext))
#
#     plaintext = unicode(base64.encodestring(os.urandom(1024 * 2 + random.randint(0, 1024))))
#     assert plaintext == k.unsealText(k.public_key.sealText(plaintext))
#
#     k2 = AsymmKeyV3(k._curve25519_secret, k._p256_secret)
#     plaintext = os.urandom(1024 * 2 + random.randint(0, 1024))
#     assert plaintext == k.unsealBinary(k2.public_key.sealBinary(plaintext))
#     assert plaintext == k2.unsealBinary(k.public_key.sealBinary(plaintext))
#
#     assert k == k2
