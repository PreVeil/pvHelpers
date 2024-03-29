from .key_protocols import ASYMM_KEY_PROTOCOL_VERSION, SYMM_KEY_PROTOCOL_VERSION, USER_KEY_PROTOCOL_VERSION, \
    SIGN_KEY_PROTOCOL_VERSION
from .user_key import UserKeyV0, PublicUserKeyV0, UserKeyV1, PublicUserKeyV1
from .symm_key import SymmKeyV0, SymmKeyV1
from .asymm_key import AsymmKeyV0, AsymmKeyV2, AsymmKeyV3, PublicKeyV3, PublicKeyV2, AsymmKeyV1, PublicKeyV1
from .sign_key import SignKeyV3, SignKeyV1, SignKeyV0, VerifyKeyV1, VerifyKeyV0, VerifyKeyV3
from .utils import CryptoException, g_log, UserKeyBuffer, ProtobufErrors, KeyBuffer, PublicUserKeyBuffer, b64dec, \
    utf8Decode, jloads, EC_SECRET_LENGTH
from pvHelpers import EncodingException

class PVKeyFactory(object):
    @staticmethod
    def newUserKey(key_version, protocol_version=USER_KEY_PROTOCOL_VERSION.Latest, encryption_key=None, signing_key=None):
        if protocol_version == USER_KEY_PROTOCOL_VERSION.V0:
            # UserKeyV0 is tied to EncryptionKeyV0, SignKeyV0 due to legacy reasons
            if not encryption_key:
                encryption_key = AsymmKeyV0()
            if not signing_key:
                signing_key = SignKeyV0()
            return UserKeyV0(key_version, encryption_key, signing_key)
        elif protocol_version == USER_KEY_PROTOCOL_VERSION.V1:
            if not encryption_key:
                encryption_key = PVKeyFactory.newAsymmKey()
            if not signing_key:
                signing_key = PVKeyFactory.newSignKey()
            return UserKeyV1(key_version, encryption_key, signing_key)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def newAsymmKey(protocol_version=ASYMM_KEY_PROTOCOL_VERSION.Latest, **kwargs):
        if protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V0:
            return AsymmKeyV0(**kwargs)
        elif protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V1:
            return AsymmKeyV1(**kwargs)
        elif protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V2:
            return AsymmKeyV2(**kwargs)
        elif protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V3:
            return AsymmKeyV3(**kwargs)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def newSignKey(protocol_version=SIGN_KEY_PROTOCOL_VERSION.Latest,  **kwargs):
        if protocol_version == SIGN_KEY_PROTOCOL_VERSION.V0:
            return SignKeyV0(**kwargs)
        elif protocol_version == SIGN_KEY_PROTOCOL_VERSION.V1:
            return SignKeyV1(**kwargs)
        elif protocol_version == SIGN_KEY_PROTOCOL_VERSION.V3:
            return SignKeyV3(**kwargs)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def newSymmKey(protocol_version=SYMM_KEY_PROTOCOL_VERSION.Latest, **kwargs):
        if protocol_version == SYMM_KEY_PROTOCOL_VERSION.V0:
            return SymmKeyV0(**kwargs)
        elif protocol_version == SYMM_KEY_PROTOCOL_VERSION.V1:
            return SymmKeyV1(**kwargs)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))


    @staticmethod
    def asymmKeyFromBuffer(buffer):
        if buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V1:
            return AsymmKeyV1(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V2:
            return AsymmKeyV2(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V3:
            return AsymmKeyV3(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version {}".format(buffer.protocol_version))

    @staticmethod
    def signKeyFromBuffer(buffer):
        if buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V1:
            return SignKeyV1(buffer.key)
        elif buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V3:
            return SignKeyV3(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version {}".format(buffer.protocol_version))

    @staticmethod
    def publicKeyFromBuffer(buffer):
        if buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V1:
            return PublicKeyV1(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V2:
            return PublicKeyV2(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V3:
            return PublicKeyV3(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version {}".format(buffer.protocol_version))

    @staticmethod
    def verifyKeyFromBuffer(buffer):
        if buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V1:
            return VerifyKeyV1(buffer.key)
        elif buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V3:
            return VerifyKeyV3(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version {}".format(buffer.protocol_version))

    @staticmethod
    def symmKeyFromSerializedBuffer(serialized_buffer):
        try:
            buffer = KeyBuffer()
            buffer.ParseFromString(serialized_buffer)
            if buffer.protocol_version == SYMM_KEY_PROTOCOL_VERSION.V1:
                return SymmKeyV1(secret=buffer.key)
            else:
                raise CryptoException(u"unsupported protocol_version {}".format(buffer.protocol_version))
        except ProtobufErrors as e:
            raise CryptoException(e)

    @staticmethod
    def userKeyFromSerializedBuffer(serialized_buffer):
        try:
            buffer = UserKeyBuffer()
            buffer.ParseFromString(serialized_buffer)
            if buffer.protocol_version == USER_KEY_PROTOCOL_VERSION.V1:
                return UserKeyV1(
                    buffer.key_version,
                    PVKeyFactory.asymmKeyFromBuffer(buffer.private_key),
                    PVKeyFactory.signKeyFromBuffer(buffer.signing_key)
                )
            else:
                raise CryptoException(u"unsupported protocol_version {}".format(buffer.protocol_version))
        except ProtobufErrors as e:
            raise CryptoException(e)

    @staticmethod
    def exportKeyFromSerializedBuffer(serialized_buffer):
        try:
            buffer = UserKeyBuffer()
            buffer.ParseFromString(serialized_buffer)
            if buffer.protocol_version == USER_KEY_PROTOCOL_VERSION.V1:
                return UserKeyV1(
                    buffer.key_version,
                    PVKeyFactory.asymmKeyFromBuffer(buffer.private_key),
                    PVKeyFactory.newSignKey()
                )
            else:
                raise CryptoException(u"unsupported protocol_version {}".format(buffer.protocol_version))
        except ProtobufErrors as e:
            raise CryptoException(e)

    @staticmethod
    def deserializeSymmKey(key):
        try:
            return PVKeyFactory.symmKeyFromSerializedBuffer(key)
        except (ProtobufErrors, CryptoException) as e:
            return SymmKeyV0.deserialize(key)


    @staticmethod
    def deserializeVerifyKey(verify_key):
        verify_key = b64dec(verify_key)
        try:
            buffer = KeyBuffer()
            buffer.ParseFromString(verify_key)
            return PVKeyFactory.verifyKeyFromBuffer(buffer)
        except (ProtobufErrors, CryptoException) as e:
            return VerifyKeyV0(verify_key)


    @staticmethod
    def deserializeAsymmKey(asymm_key):
        asymm_key = b64dec(asymm_key)
        try:
            buffer = KeyBuffer()
            buffer.ParseFromString(asymm_key)
            return PVKeyFactory.asymmKeyFromBuffer(buffer)
        except (ProtobufErrors, CryptoException) as e:
            return AsymmKeyV0(asymm_key)

    @staticmethod
    def deserializeSignKey(sign_key):
        sign_key = b64dec(sign_key)
        try:
            buffer = KeyBuffer()
            buffer.ParseFromString(sign_key)
            return PVKeyFactory.signKeyFromBuffer(buffer)
        except (ProtobufErrors, CryptoException) as e:
            return SignKeyV0(sign_key)


    @staticmethod
    def deserializePublicUserKey(public_user_key, is_protobuf=True):
        if not is_protobuf:
            try:
                return PublicUserKeyV0.deserialize(public_user_key)
            except (EncodingException, CryptoException) as e:
                pass

        serialized = b64dec(public_user_key)
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
                raise CryptoException(u"unsupported protocol_version {}".format(buffer.protocol_version))
        except ProtobufErrors as e:
            raise CryptoException(e)

    @staticmethod
    def deserializeUserKey(user_key, is_protobuf=True):
        if not is_protobuf:
            try:
                return UserKeyV0.deserialize(user_key)
            except (EncodingException, CryptoException) as e:
                pass

        serialized = b64dec(user_key)
        return PVKeyFactory.userKeyFromSerializedBuffer(serialized)

    @staticmethod
    def deserializeExportKey(user_key):
        serialized = b64dec(user_key)
        return PVKeyFactory.exportKeyFromSerializedBuffer(serialized)
        
    @staticmethod
    def userKeyfromDB(key, is_protobuf=True):
        if is_protobuf:
            return PVKeyFactory.deserializeUserKey(key, True)
        else:
            key = UserKeyV0.fromDB(key)
            return PVKeyFactory.newUserKey(key.key_version, USER_KEY_PROTOCOL_VERSION.V1, AsymmKeyV1(key.encryption_key.sk), SignKeyV1(key.signing_key.seed))
