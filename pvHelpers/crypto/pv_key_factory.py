from .key_protocols import ASYMM_KEY_PROTOCOL_VERSION, SYMM_KEY_PROTOCOL_VERSION, USER_KEY_PROTOCOL_VERSION, SIGN_KEY_PROTOCOL_VERSION
from .user_key import UserKeyV0, PublicUserKeyV0, UserKeyV1, PublicUserKeyV1
from .symm_key import SymmKeyV0
from .asymm_key import AsymmKeyV0, AsymmKeyV2, PublicKeyV2, AsymmKeyV1, PublicKeyV1
from .sign_key import SignKeyV1, SignKeyV0, VerifyKeyV1, VerifyKeyV0
from .utils import CryptoException, g_log, UserKeyBuffer, ProtobufErrors, KeyBuffer, PublicUserKeyBuffer, b64dec, utf8Decode, jloads

class PVKeyFactory(object):
    @staticmethod
    def newUserKey(key_version, protocol_version=USER_KEY_PROTOCOL_VERSION.Latest, encryption_key=None, signing_key=None):
        if protocol_version == USER_KEY_PROTOCOL_VERSION.V0:
            if not encryption_key:
                encryption_key = AsymmKeyV0()
            if not signing_key:
                signing_key = SignKeyV0()
            return UserKeyV0(key_version, encryption_key, signing_key)
        elif protocol_version == USER_KEY_PROTOCOL_VERSION.V1:
            if not encryption_key:
                encryption_key = AsymmKeyV2()
            if not signing_key:
                signing_key = SignKeyV1()
            return UserKeyV1(key_version, encryption_key, signing_key)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def newSymmKey(protocol_version=SYMM_KEY_PROTOCOL_VERSION.Latest, *args, **kwargs):
        if protocol_version == SYMM_KEY_PROTOCOL_VERSION.V0:
            return SymmKeyV0(*args, **kwargs)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def asymmKeyFromBuffer(buffer):
        if buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V1:
            return AsymmKeyV1(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V2:
            return AsymmKeyV2(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version")

    @staticmethod
    def signKeyFromBuffer(buffer):
        if buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V1:
            return SignKeyV1(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version")

    @staticmethod
    def publicKeyFromBuffer(buffer):
        if buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V1:
            return PublicKeyV1(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V2:
            return PublicKeyV2(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version")

    @staticmethod
    def verifyKeyFromBuffer(buffer):
        if buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V1:
            return VerifyKeyV1(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version")

    @staticmethod
    def deserializeSymmKey(key):
        return SymmKeyV0.fromDict({"key": key})

    @staticmethod
    def deserializeVerifyKey(verify_key):
        status, verify_key = b64dec(verify_key)
        if not status:
            raise CryptoException(u"Failed b64 dec")
        try:
            buffer = KeyBuffer()
            buffer.ParseFromString(verify_key)
            return PVKeyFactory.verifyKeyFromBuffer(buffer)
        except (ProtobufErrors, CryptoException) as e:
            g_log.exception(e)
            g_log.info(u"Falling back to protocol_version 0")

        return VerifyKeyV0(verify_key)

    @staticmethod
    def deserializePublicUserKey(public_user_key, is_protobuf=True):
        if not is_protobuf:
            try:
                return PublicUserKeyV0.deserialize(public_user_key)
            except CryptoException as e:
                g_log.exception(e)
                g_log.info("Falling to protobuf")

        status, serialized = b64dec(public_user_key)
        if not status:
            raise CryptoException(u"Failed to b64 dec key")
        try:
            buffer = PublicUserKeyBuffer()
            buffer.ParseFromString(serialized)
            if buffer.protocol_version == USER_KEY_PROTOCOL_VERSION.V1:
                return PublicUserKeyV1(
                    buffer.key_version,
                    PVKeyFactory.publicKeyFromBuffer(buffer.public_key),
                    PVKeyFactory.verifyKeyFromBuffer(buffer.verify_key)
                )
            else:
                raise CryptoException(u"unsupported protocol_version")
        except ProtobufErrors as e:
            raise CryptoException(e)

    @staticmethod
    def deserializeUserKey(user_key, is_protobuf=True):
        if not is_protobuf:
            try:
                return UserKeyV0.deserialize(user_key)
            except CryptoException as e:
                g_log.exception(e)
                g_log.info("Falling to protobuf")

        status, serialized = b64dec(user_key)
        if not status:
            raise CryptoException(u"Failed to b64 dec key")
        try:
            buffer = UserKeyBuffer()
            buffer.ParseFromString(serialized)
            if buffer.protocol_version == USER_KEY_PROTOCOL_VERSION.V1:
                return UserKeyV1(
                    buffer.key_version,
                    PVKeyFactory.asymmKeyFromBuffer(buffer.private_key),
                    PVKeyFactory.signKeyFromBuffer(buffer.signing_key)
                )
            else:
                raise CryptoException(u"unsupported protocol_version")
        except ProtobufErrors as e:
            raise CryptoException(e)



    @staticmethod
    def userKeyfromDB(key, is_protobuf=True):
        if is_protobuf:
            return PVKeyFactory.deserializeUserKey(key, True)
        else:
            key = UserKeyV0.fromDB(key)
            return PVKeyFactory.newUserKey(key.key_version, USER_KEY_PROTOCOL_VERSION.V1, AsymmKeyV1(key.encryption_key.sk), SignKeyV1(key.signing_key.seed))
