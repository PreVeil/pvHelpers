import datetime
import sys
import types
import uuid

import pvHelpers as H

CURRENT_PLATFORM = u"windows" if sys.platform == "win32" else \
                u"macos" if sys.platform == "darwin" else \
                u"linux" if sys.platform == "linux2" else sys.platform

class DeviceStatus(object):
    LOCAL = u"local"
    ACTIVE = u"active"
    EXPIRED = u"expired"
    LOCKED = u"locked"

class Device(object):
    @H.params(object, unicode, {types.NoneType, unicode}, H.PublicUserKeyBase, dict, unicode, unicode)
    def __init__(self, id_, name, public_key, metadata, status, platform):
        self.id = id_
        self.name = name
        self._public_key = public_key
        self.metadata = metadata
        self.status = status
        self.platform = platform

    @property
    def public_key(self):
        return self._public_key

    def toDict(self):
        return {
            "device_id": self.id,
            "device_name": self.name if self.name else None,
            "public_key": self.public_key.serialize(),
            "metadata": self.metadata,
            "platform": self.platform
        }

    @classmethod
    def fromDict(cls, device_data):
        return cls(
            device_data["device_id"],
            device_data["device_name"],
            H.PVKeyFactory.deserializePublicUserKey(device_data["public_key"]),
            device_data["metadata"],
            device_data.get("status", DeviceStatus.LOCAL),
            device_data["platform"]
        )
