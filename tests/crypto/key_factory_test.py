import os, base64, random

from pvHelpers import USER_KEY_PROTOCOL_VERSION, ASYMM_KEY_PROTOCOL_VERSION, SYMM_KEY_PROTOCOL_VERSION, \
    SIGN_KEY_PROTOCOL_VERSION, PVKeyFactory, CryptoException
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
    k2 = PVKeyFactory.newAsymmKey(protocol_version=protocol_version, key=k.key)

    assert k == k2
    assert k.protocol_version == protocol_version
    assert k == PVKeyFactory.deserializeAsymmKey(k.serialize())

    # unknown protocol_version
    with pytest.raises(CryptoException) as ex:
        PVKeyFactory.newAsymmKey(protocol_version=9999)


@pytest.mark.parametrize('protocol_version', [
    SIGN_KEY_PROTOCOL_VERSION.V0,
    SIGN_KEY_PROTOCOL_VERSION.V1,
    SIGN_KEY_PROTOCOL_VERSION.V3,
])
def test_sign_key_creation(protocol_version):
    k = PVKeyFactory.newSignKey(protocol_version)
    k2 = PVKeyFactory.newSignKey(protocol_version=protocol_version, key=k.key)

    assert k == k2
    assert k.protocol_version == protocol_version
    assert k == PVKeyFactory.deserializeSignKey(k.serialize())

    # verify side
    vk, vk2 = k.verify_key, k2.verify_key
    assert vk2.serialize() == PVKeyFactory.deserializeVerifyKey(vk.serialize()).serialize()

    # unknown protocol_version
    with pytest.raises(CryptoException) as ex:
        PVKeyFactory.newSignKey(protocol_version=9999)


@pytest.mark.parametrize('protocol_version', [
    SYMM_KEY_PROTOCOL_VERSION.V0,
    SYMM_KEY_PROTOCOL_VERSION.V1,
])
def test_symm_key_creation(protocol_version):
    k = PVKeyFactory.newSymmKey(protocol_version)
    k2 = PVKeyFactory.newSymmKey(protocol_version=protocol_version, secret=k.secret)
    assert k.protocol_version == protocol_version
    assert k == k2
    assert k == PVKeyFactory.deserializeSymmKey(k2.serialize())

    # unknown protocol_version
    with pytest.raises(CryptoException) as ex:
        PVKeyFactory.newSymmKey(protocol_version=9999)
