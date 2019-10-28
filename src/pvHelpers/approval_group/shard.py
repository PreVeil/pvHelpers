from pvHelpers.crypto import (ASYMM_KEY_PROTOCOL_VERSION,
                              SIGN_KEY_PROTOCOL_VERSION)
from pvHelpers.crypto.box import AsymmBox
from pvHelpers.crypto.user_key import PublicUserKeyBase, UserKeyBase
from pvHelpers.utils import b64dec, b64enc, jdumps, jloads, params


class ENCRYPTED_SHARD_VERSIONS(object):
    V1 = 1
    V2 = 2

    Latest = 1

class EncryptedShardV1(object):
    protocol_version = 1

    @params(object, unicode, {int, long}, unicode, bool)
    def __init__(self, sharee_user_id, sharee_key_version, secret, required=False):
        self.sharee_user_id = sharee_user_id
        self.sharee_key_version = sharee_key_version
        self.secret = secret
        self.required = required

    @classmethod
    @params(object, UserKeyBase, unicode, PublicUserKeyBase, bytes, bool)
    def new(cls, sharer_key, sharee_id, sharee_key, raw_shard, required=False):
        box = AsymmBox(sharer_key.encryption_key, sharee_key.public_key)
        return cls(sharee_id, sharee_key.key_version, b64enc(box.encrypt(raw_shard)), required)

    @params(object, UserKeyBase, PublicUserKeyBase)
    def decryptShard(self, sharee_key, sharer_key):
        if sharee_key.key_version != self.sharee_key_version:
            raise ValueError(u"provided key has wrong key_version {}".format(sharee_key.key_version))
        box = AsymmBox(sharee_key.encryption_key, sharer_key.public_key)
        return box.decrypt(b64dec(self.secret))

    def toDict(self):
        return {
            "user_id": self.sharee_user_id,
            "key_version": self.sharee_key_version,
            "secret": self.secret,
            "protocol_version": self.protocol_version,
            "required": self.required
        }


class EncryptedShardV2(EncryptedShardV1):
    protocol_version = 2

    @classmethod
    @params(object, UserKeyBase, unicode, PublicUserKeyBase, bytes, bool)
    def new(cls, sharer_key, sharee_id, sharee_key, raw_shard, required=False):
        return cls(sharee_id, sharee_key.key_version, jdumps({
            "shard": b64enc(sharee_key.public_key.seal(raw_shard)),
            "signature": b64enc(sharer_key.signing_key.sign(raw_shard))
        }), required)

    @params(object, UserKeyBase, PublicUserKeyBase)
    def decryptShard(self, sharee_key, sharer_key):
        if sharee_key.key_version != self.sharee_key_version:
            raise ValueError(u"provided key has wrong key_version {}".format(sharee_key.key_version))

        secret_dict = jloads(self.secret)
        raw_shard = sharee_key.encryption_key.unseal(b64dec(secret_dict["shard"]))
        if not sharer_key.verify_key.verify(raw_shard, b64dec(secret_dict["signature"])):
            raise CryptoException("signature verification failed")

        return raw_shard


def new(sharer_key, sharee_id, sharee_public_user_key, raw_shard, required):
    if sharer_key.signing_key.protocol_version > SIGN_KEY_PROTOCOL_VERSION.V1 or \
        sharee_public_user_key.public_key.protocol_version > ASYMM_KEY_PROTOCOL_VERSION.V2:
        return EncryptedShardV2.new(
            sharer_key, sharee_id, sharee_public_user_key, raw_shard, required)
    else:
        return EncryptedShardV1.new(
            sharer_key, sharee_id, sharee_public_user_key, raw_shard, required)


def fromDict(shard_info):
    protocol_version = shard_info.get("protocol_version", 1)
    if protocol_version == ENCRYPTED_SHARD_VERSIONS.V1:
        return EncryptedShardV1(
            shard_info["user_id"], shard_info["key_version"], shard_info["secret"], shard_info["required"])
    elif protocol_version == ENCRYPTED_SHARD_VERSIONS.V2:
        return EncryptedShardV2(
            shard_info["user_id"], shard_info["key_version"], shard_info["secret"], shard_info["required"])
    else:
        raise ValueError("unsupported protocol_version {}".format(protocol_version))
