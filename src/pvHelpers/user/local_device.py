import types
import uuid

from pvHelpers.crypto import PVKeyFactory
from pvHelpers.crypto.user_key import UserKeyBase
from pvHelpers.utils import params

from .device import CURRENT_PLATFORM, Device, DeviceStatus


class LocalDevice(Device):
    @params(object, unicode, {types.NoneType, unicode}, UserKeyBase, dict, unicode, unicode)
    def __init__(self, id_, name, key, metadata, status, platform=CURRENT_PLATFORM):
        super(LocalDevice, self).__init__(id_, name, key.public_user_key, metadata, status, platform)
        self.key = key

    @property
    def public_key(self):
        return self.key.public_user_key

    def to_db(self):
        return {
            "device_id": self.id,
            "device_name": self.name,
            "key": self.key.serialize(),
            "metadata": self.metadata,
            "status": self.status
        }

    @classmethod
    def new(cls, key_version=1):
        return cls(
            unicode(uuid.uuid4()), None,
            PVKeyFactory.new_user_key(key_version), {}, DeviceStatus.LOCAL
        )

    @classmethod
    def from_db(cls, device_data):
        return cls(
            device_data["device_id"],
            device_data["device_name"],
            PVKeyFactory.user_key_from_db(device_data["key"]),
            device_data["metadata"],
            device_data["status"]
        )

    def __eq__(self, other):
        return isinstance(other, LocalDevice) and \
            self.id == other.id and \
            self.name == other.name and \
            self.key == other.key

    def __ne__(self, other):
        return not self.__eq__(other)
