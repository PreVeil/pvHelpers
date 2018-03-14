from .key_protocols import ASYMM_KEY_PROTOCOL_VERSION, SYMM_KEY_PROTOCOL_VERSION, USER_KEY_PROTOCOL_VERSION
from .user_key import UserKeyV0, PublicUserKeyV0
from .symm_key import SymmKeyV0
from .utils import CryptoException, jloads, g_log

class PVKeyFactory(object):
    @staticmethod
    def newUserKey(key_version, protocol_version=USER_KEY_PROTOCOL_VERSION.Latest, *args, **kwargs):
        if protocol_version == USER_KEY_PROTOCOL_VERSION.V0:
            return UserKeyV0(key_version, *args, **kwargs)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def newSymmKey(protocol_version=SYMM_KEY_PROTOCOL_VERSION.Latest, *args, **kwargs):
        if protocol_version == SYMM_KEY_PROTOCOL_VERSION.V0:
            return SymmKeyV0(*args, **kwargs)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def deserializeSymmKey(key):
        return SymmKeyV0.fromDict({"key": key})

    @staticmethod
    def deserializeUserKey(json):
        status, key_dict = jloads(json)
        if status == False:
            raise CryptoException("Failed to deserialize key json string")

        protocol_version = key_dict.get("protocol_version")
        if protocol_version is None or protocol_version == USER_KEY_PROTOCOL_VERSION.V0:
            return UserKeyV0.fromDict(key_dict)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def deserializePublicUserKey(key):
        if isinstance(key, dict):
            return PublicUserKeyV0.fromDict(key)
        else:
            raise CryptoException("Invalid protocol_version")
