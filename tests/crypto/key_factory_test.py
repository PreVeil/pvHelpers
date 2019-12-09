from pvHelpers.crypto import (ASYMM_KEY_PROTOCOL_VERSION, PVKeyFactory,
                              SIGN_KEY_PROTOCOL_VERSION,
                              SYMM_KEY_PROTOCOL_VERSION,
                              USER_KEY_PROTOCOL_VERSION)
from pvHelpers.crypto.utils import CryptoException
import pytest


@pytest.mark.parametrize('protocol_version', [
    USER_KEY_PROTOCOL_VERSION.V1
])
def test_user_key_creation(protocol_version):
    key = PVKeyFactory.new_user_key(0)
    assert key.protocol_version == USER_KEY_PROTOCOL_VERSION.Latest

    for key_version in range(0, 222):
        k = PVKeyFactory.new_user_key(key_version, protocol_version)
        k2 = PVKeyFactory.new_user_key(
            key_version, k.protocol_version, k.encryption_key, k.signing_key)
        assert k == k2
        assert k.key_version == key_version
        assert k.protocol_version == protocol_version
        assert k.encryption_key.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.Latest
        assert k.signing_key.protocol_version == SIGN_KEY_PROTOCOL_VERSION.Latest
        assert k2.serialize() == k.serialize()
        assert k == PVKeyFactory.deserialize_user_key(k.serialize())

    # unknown protocol_version
    with pytest.raises(CryptoException):
        PVKeyFactory.new_user_key(0, protocol_version=9999)


@pytest.mark.parametrize('protocol_version', [
    ASYMM_KEY_PROTOCOL_VERSION.V0,
    ASYMM_KEY_PROTOCOL_VERSION.V1,
    ASYMM_KEY_PROTOCOL_VERSION.V2,
    ASYMM_KEY_PROTOCOL_VERSION.V3,
])
def test_encryption_key_creation(protocol_version):
    k = PVKeyFactory.new_asymm_key(protocol_version)
    k2 = PVKeyFactory.new_asymm_key(protocol_version=protocol_version, key=k.key)

    assert k == k2
    assert k.protocol_version == protocol_version
    assert k == PVKeyFactory.deserialize_asymm_key(k.serialize())

    # unknown protocol_version
    with pytest.raises(CryptoException):
        PVKeyFactory.new_asymm_key(protocol_version=9999)


@pytest.mark.parametrize('protocol_version', [
    SIGN_KEY_PROTOCOL_VERSION.V0,
    SIGN_KEY_PROTOCOL_VERSION.V1,
    SIGN_KEY_PROTOCOL_VERSION.V3,
])
def test_sign_key_creation(protocol_version):
    k = PVKeyFactory.new_sign_key(protocol_version)
    k2 = PVKeyFactory.new_sign_key(protocol_version=protocol_version, key=k.key)

    assert k == k2
    assert k.protocol_version == protocol_version
    assert k == PVKeyFactory.deserialize_sign_key(k.serialize())

    # verify side
    vk, vk2 = k.verify_key, k2.verify_key
    assert vk2.serialize() == PVKeyFactory.deserialize_verify_key(vk.serialize()).serialize()

    # unknown protocol_version
    with pytest.raises(CryptoException):
        PVKeyFactory.new_sign_key(protocol_version=9999)


@pytest.mark.parametrize('protocol_version', [
    SYMM_KEY_PROTOCOL_VERSION.V0,
    SYMM_KEY_PROTOCOL_VERSION.V1,
])
def test_symm_key_creation(protocol_version):
    k = PVKeyFactory.new_symm_key(protocol_version)
    k2 = PVKeyFactory.new_symm_key(protocol_version=protocol_version, secret=k.secret)
    assert k.protocol_version == protocol_version
    assert k == k2
    assert k == PVKeyFactory.deserialize_symm_key(k2.serialize())

    # unknown protocol_version
    with pytest.raises(CryptoException):
        PVKeyFactory.new_symm_key(protocol_version=9999)
