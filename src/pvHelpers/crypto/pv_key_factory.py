from pvHelpers.crypto.asymm_key import (AsymmKeyV0, AsymmKeyV1, AsymmKeyV2,
                                        AsymmKeyV3, PublicKeyV1, PublicKeyV2,
                                        PublicKeyV3)
from pvHelpers.crypto.sign_key import (SignKeyV0, SignKeyV1, SignKeyV3,
                                       VerifyKeyV0, VerifyKeyV1, VerifyKeyV3)
from pvHelpers.crypto.symm_key import SymmKeyV0, SymmKeyV1
from pvHelpers.crypto.user_key import (PublicUserKeyV0, PublicUserKeyV1,
                                       UserKeyV0, UserKeyV1)
from pvHelpers.protos import Key as KeyBuffer
from pvHelpers.protos import ProtobufErrors
from pvHelpers.protos import PublicUserKey as PublicUserKeyBuffer
from pvHelpers.protos import UserKey as UserKeyBuffer
from pvHelpers.utils import b64dec, EncodingException

from .key_protocols import (ASYMM_KEY_PROTOCOL_VERSION,
                            SIGN_KEY_PROTOCOL_VERSION,
                            SYMM_KEY_PROTOCOL_VERSION,
                            USER_KEY_PROTOCOL_VERSION)
from .utils import CryptoException


class PVKeyFactory(object):
    @staticmethod
    def new_user_key(key_version, protocol_version=USER_KEY_PROTOCOL_VERSION.Latest,
                     encryption_key=None, signing_key=None):
        if protocol_version == USER_KEY_PROTOCOL_VERSION.V0:
            # UserKeyV0 is tied to EncryptionKeyV0, SignKeyV0 due to legacy reasons
            if not encryption_key:
                encryption_key = AsymmKeyV0()
            if not signing_key:
                signing_key = SignKeyV0()
            return UserKeyV0(key_version, encryption_key, signing_key)
        elif protocol_version == USER_KEY_PROTOCOL_VERSION.V1:
            if not encryption_key:
                encryption_key = PVKeyFactory.new_asymm_key()
            if not signing_key:
                signing_key = PVKeyFactory.new_sign_key()
            return UserKeyV1(key_version, encryption_key, signing_key)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def new_asymm_key(protocol_version=ASYMM_KEY_PROTOCOL_VERSION.Latest, **kwargs):
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
    def new_sign_key(protocol_version=SIGN_KEY_PROTOCOL_VERSION.Latest,  **kwargs):
        if protocol_version == SIGN_KEY_PROTOCOL_VERSION.V0:
            return SignKeyV0(**kwargs)
        elif protocol_version == SIGN_KEY_PROTOCOL_VERSION.V1:
            return SignKeyV1(**kwargs)
        elif protocol_version == SIGN_KEY_PROTOCOL_VERSION.V3:
            return SignKeyV3(**kwargs)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def new_symm_key(protocol_version=SYMM_KEY_PROTOCOL_VERSION.Latest, **kwargs):
        if protocol_version == SYMM_KEY_PROTOCOL_VERSION.V0:
            return SymmKeyV0(**kwargs)
        elif protocol_version == SYMM_KEY_PROTOCOL_VERSION.V1:
            return SymmKeyV1(**kwargs)
        else:
            raise CryptoException("Invalid protocol_version: {}".format(protocol_version))

    @staticmethod
    def asymm_key_from_buffer(buffer):
        if buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V1:
            return AsymmKeyV1(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V2:
            return AsymmKeyV2(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V3:
            return AsymmKeyV3(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version {}".format(buffer.protocol_version))

    @staticmethod
    def sign_key_from_buffer(buffer):
        if buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V1:
            return SignKeyV1(buffer.key)
        elif buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V3:
            return SignKeyV3(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version {}".format(buffer.protocol_version))

    @staticmethod
    def public_key_from_buffer(buffer):
        if buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V1:
            return PublicKeyV1(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V2:
            return PublicKeyV2(buffer.key)
        elif buffer.protocol_version == ASYMM_KEY_PROTOCOL_VERSION.V3:
            return PublicKeyV3(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version {}".format(buffer.protocol_version))

    @staticmethod
    def verify_key_from_buffer(buffer):
        if buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V1:
            return VerifyKeyV1(buffer.key)
        elif buffer.protocol_version == SIGN_KEY_PROTOCOL_VERSION.V3:
            return VerifyKeyV3(buffer.key)
        else:
            raise CryptoException(u"not supported protocol_version {}".format(buffer.protocol_version))

    @staticmethod
    def symm_key_from_serialized_buffer(serialized_buffer):
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
    def user_key_from_serialized_buffer(serialized_buffer):
        try:
            buffer = UserKeyBuffer()
            buffer.ParseFromString(serialized_buffer)
            if buffer.protocol_version == USER_KEY_PROTOCOL_VERSION.V1:
                return UserKeyV1(
                    buffer.key_version,
                    PVKeyFactory.asymm_key_from_buffer(buffer.private_key),
                    PVKeyFactory.sign_key_from_buffer(buffer.signing_key)
                )
            else:
                raise CryptoException(u"unsupported protocol_version {}".format(buffer.protocol_version))
        except ProtobufErrors as e:
            raise CryptoException(e)

    @staticmethod
    def deserialize_symm_key(key):
        try:
            return PVKeyFactory.symm_key_from_serialized_buffer(key)
        except (ProtobufErrors, CryptoException):
            return SymmKeyV0.deserialize(key)

    @staticmethod
    def deserialize_verify_key(verify_key):
        verify_key = b64dec(verify_key)
        try:
            buffer = KeyBuffer()
            buffer.ParseFromString(verify_key)
            return PVKeyFactory.verify_key_from_buffer(buffer)
        except (ProtobufErrors, CryptoException):
            return VerifyKeyV0(verify_key)

    @staticmethod
    def deserialize_asymm_key(asymm_key):
        asymm_key = b64dec(asymm_key)
        try:
            buffer = KeyBuffer()
            buffer.ParseFromString(asymm_key)
            return PVKeyFactory.asymm_key_from_buffer(buffer)
        except (ProtobufErrors, CryptoException):
            return AsymmKeyV0(asymm_key)

    @staticmethod
    def deserialize_sign_key(sign_key):
        sign_key = b64dec(sign_key)
        try:
            buffer = KeyBuffer()
            buffer.ParseFromString(sign_key)
            return PVKeyFactory.sign_key_from_buffer(buffer)
        except (ProtobufErrors, CryptoException):
            return SignKeyV0(sign_key)

    @staticmethod
    def deserialize_public_user_key(public_user_key, is_protobuf=True):
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
                    PVKeyFactory.public_key_from_buffer(buffer.public_key),
                    PVKeyFactory.verify_key_from_buffer(buffer.verify_key)
                )
            else:
                raise CryptoException(u"unsupported protocol_version {}".format(buffer.protocol_version))
        except ProtobufErrors as e:
            raise CryptoException(e)

    @staticmethod
    def deserialize_user_key(user_key, is_protobuf=True):
        if not is_protobuf:
            try:
                return UserKeyV0.deserialize(user_key)
            except (EncodingException, CryptoException):
                pass

        serialized = b64dec(user_key)
        return PVKeyFactory.user_key_from_serialized_buffer(serialized)

    @staticmethod
    def user_key_from_db(key, is_protobuf=True):
        if is_protobuf:
            return PVKeyFactory.deserialize_user_key(key, True)
        else:
            key = UserKeyV0.from_db(key)
            return PVKeyFactory.new_user_key(
                key.key_version, USER_KEY_PROTOCOL_VERSION.V1,
                AsymmKeyV1(key.encryption_key.sk), SignKeyV1(key.signing_key.seed))
