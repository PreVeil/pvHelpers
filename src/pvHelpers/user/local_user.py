import types

from pvHelpers.crypto import UserKeyBase
from pvHelpers.utils import NOT_ASSIGNED, params

from .local_device import LocalDevice
from .luser_info import LUserInfo
from .user import OrganizationInfo, User


class LocalUser(User):
    @params(object, unicode, unicode, unicode, {OrganizationInfo, types.NoneType}, {NOT_ASSIGNED, LUserInfo}, unicode, [UserKeyBase], {types.NoneType, LocalDevice})
    def __init__(self, user_id, display_name, mail_cid, org_info, luser_info, password, user_keys, device):
        super(LocalUser, self).__init__(user_id, display_name, mail_cid, map(lambda k: k.public_user_key, user_keys), org_info)
        self.luser_info = luser_info
        self.user_keys = user_keys
        self.password = password
        self.device = device

    @property
    def user_key(self):
        if not self.user_keys:
            raise ValueError("No User keys available!")

        return sorted(self.user_keys, key=lambda k: k.key_version, reverse=True)[0]

    def signWithUserKey(self, data):
        return self.user_key.key_version, self.user_key.signing_key.sign(data)

    def signWithDeviceKey(self, data):
        if not self.device:
            raise KeyError("User missing device key")
        return self.device.key.key_version, self.device.key.signing_key.sign(data)

    @params(object, {int, long})
    def getKeyWithVersion(self, version=-1):
        if version == -1:
            return self.user_key
        return next(k for k in self.user_keys if k.key_version == version)

    def hasDeviceKey(self):
        return self.device is not None

    def toDict(self):
        # NOTE: this method is used when serializing user info to respond
        # to clients. MUST not expose user keys in this.
        return MergeDicts(super(LocalUser, self).toDict(), {
            "public_user_key": self.public_user_key.serialize(),
            "password": self.password,
            "luser_info": str(self.luser_info),
            "device":  self.device.toDict() if self.hasDeviceKey() else None,
            "user_key_versions": map(lambda k: k.key_version, self.user_keys)
        })
