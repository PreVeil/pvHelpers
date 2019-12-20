import types

from pvHelpers.crypto.asymm_key import AsymmKeyBase
from pvHelpers.crypto.user_key import UserKeyBase
from pvHelpers.utils import params

from .client import CryptoClient


class RemoteAsymmKey(AsymmKeyBase):
    @params(object, CryptoClient, unicode, int, {types.NoneType, int})
    def __init__(self, client, user_id, key_version, protocol_version=0):
        super(RemoteAsymmKey, self).__init__(protocol_version)
        self.client = client
        self.user_id = user_id
        self.key_version = key_version

    @params(object, bytes)
    def unseal(self, cipher):
        return self.client.user_key_decrypt(self.user_id, self.key_version, cipher)


class RemoteUserKey(UserKeyBase):
    @params(object, CryptoClient, unicode, int, {types.NoneType, int})
    def __init__(self, client, user_id, key_version, protocol_version=0):
        super(RemoteUserKey, self).__init__(protocol_version, key_version)
        self.client = client
        self.user_id = user_id
        self.key_version = key_version
        self.encryption_key = RemoteAsymmKey(client, user_id, key_version)
