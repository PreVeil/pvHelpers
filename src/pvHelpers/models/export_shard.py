from pvHelpers.utils import b64dec, b64enc, jdumps, jloads, params
from pvHelpers.crypto.box import AsymmBox
from pvHelpers.crypto.user_key import UserKeyBase, PublicUserKeyBase
from pvHelpers.crypto import SIGN_KEY_PROTOCOL_VERSION, ASYMM_KEY_PROTOCOL_VERSION

class EXPORT_ENCRYPTED_SHARD_VERSIONS(object):
    V1 = 1
    V2 = 2

    Latest = 1


class ExportEncryptedShardV1(object):
    protocol_version = 1


    @params(object, unicode, {int, long}, {int, long}, {int, long}, unicode, bool)
    def __init__(self, sharee_user_id, sharee_key_version, sharer_key_version, wrapped_key_version, secret, required=False):
        self.sharee_user_id = sharee_user_id
        self.sharee_key_version = sharee_key_version
        self.sharer_key_version = sharer_key_version
        self.wrapped_key_version = wrapped_key_version
        self.secret = secret
        self.required = required


    @classmethod
    @params(object, UserKeyBase, unicode, PublicUserKeyBase, {int, long}, bytes, bool)
    def new(cls, sharer_key, sharee_id, sharee_key, sharded_key_version, raw_shard, required=False):
        box = AsymmBox(sharer_key.encryption_key, sharee_key.public_key)
        return cls(
            sharee_id, sharee_key.key_version, sharer_key.key_version,
            sharded_key_version, b64enc(box.encrypt(raw_shard)), required)


    @params(object, UserKeyBase, PublicUserKeyBase)
    def decryptShard(self, sharee_key, sharer_key):
        if sharee_key.key_version != self.sharee_key_version:
            raise ValueError(u"provided key has wrong key_version {}".format(sharee_key.key_version))
        if sharer_key.key_version != self.sharer_key_version:
            raise ValueError(u"provided key has wrong key_version {}".format(sharer_key.key_version))
        box = AsymmBox(sharee_key.encryption_key, sharer_key.public_key)
        return box.decrypt(b64dec(self.secret))


    def toDict(self):
        return {
            "user_id": self.sharee_user_id,
            "key_version": self.sharee_key_version,
            "wrapped_key_version": self.wrapped_key_version,
            "sharder_key_version": self.sharer_key_version,
            "secret": self.secret,
            "required": self.required,
            "protocol_version": self.protocol_version
        }


class ExportEncryptedShardV2(ExportEncryptedShardV1):
    protocol_version = 2


    @classmethod
    @params(object, UserKeyBase, unicode, PublicUserKeyBase, {int, long}, bytes, bool)
    def new(cls, sharer_key, sharee_id, sharee_key, sharded_key_version, raw_shard, required=False):
        return cls(
            sharee_id, sharee_key.key_version, sharer_key.key_version,
            sharded_key_version, jdumps({
            "shard": b64enc(sharee_key.public_key.seal(raw_shard)),
            "signature": b64enc(sharer_key.signing_key.sign(raw_shard))
        }), required)


    @params(object, UserKeyBase, PublicUserKeyBase)
    def decryptShard(self, sharee_key, sharer_key):
        if sharee_key.key_version != self.sharee_key_version:
            raise ValueError(u"provided key has wrong key_version {}".format(sharee_key.key_version))
        if sharer_key.key_version != self.sharer_key_version:
            raise ValueError(u"provided key has wrong key_version {}".format(sharer_key.key_version))

        secret_dict = jloads(self.secret)
        raw_shard = sharee_key.encryption_key.unseal(b64dec(secret_dict["shard"]))
        if not sharer_key.verify_key.verify(raw_shard, b64dec(secret_dict["signature"])):
            raise CryptoException("signature verification failed")

        return raw_shard


# NOTE: making sure that V2 scheme is used when any of the sides have fips enabled keys
def new(sharer_key, sharee_id, sharee_public_user_key, sharded_key_version, raw_shard, required):
    if sharer_key.signing_key.protocol_version > SIGN_KEY_PROTOCOL_VERSION.V1 or \
        sharee_public_user_key.public_key.protocol_version > ASYMM_KEY_PROTOCOL_VERSION.V2:
        return ExportEncryptedShardV2.new(
            sharer_key, sharee_id, sharee_public_user_key, sharded_key_version, raw_shard, required)
    else:
        return ExportEncryptedShardV1.new(
            sharer_key, sharee_id, sharee_public_user_key, sharded_key_version, raw_shard, required)


def fromDict(shard_info):
    protocol_version = shard_info.get("protocol_version", 1)
    if protocol_version == EXPORT_ENCRYPTED_SHARD_VERSIONS.V1:
        return ExportEncryptedShardV1(
            shard_info["user_id"], shard_info["key_version"], shard_info["sharder_key_version"],
            shard_info["wrapped_key_version"], shard_info["secret"], shard_info["required"])
    elif protocol_version == EXPORT_ENCRYPTED_SHARD_VERSIONS.V2:
        return ExportEncryptedShardV2(
            shard_info["user_id"], shard_info["key_version"], shard_info["sharder_key_version"],
            shard_info["wrapped_key_version"], shard_info["secret"], shard_info["required"])
    else:
        raise ValueError("unsupported protocol_version {}".format(protocol_version))
