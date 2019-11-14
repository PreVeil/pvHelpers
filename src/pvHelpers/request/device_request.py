import datetime

from pvHelpers.user import LocalDevice
from pvHelpers.utils import jdumps, params


class DeviceRequest(object):
    @classmethod
    @params(object, unicode, LocalDevice)
    def new_for_recovery(cls, user_id, device):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=7)
        return cls(device, jdumps({
            "user_id": user_id,
            "type": "add_device",
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "data": device.to_dict()
        }), [])

    @classmethod
    @params(object, unicode, LocalDevice)
    def new_for_transfer(cls, user_id, device):
        return cls(device, jdumps(device.to_dict()), [])

    def __init__(self, device, serialized_req, signatures):
        self.device = device
        self.serialized_req = serialized_req
        self.signatures = signatures

    def to_db(self):
        return {
            "device": self.device.to_db(),
            "serialized_req": self.serialized_req,
            "signatures": self.signatures
        }

    @classmethod
    def from_db(cls, request_dict):
        return cls(
            LocalDevice.from_db(request_dict["device"]),
            request_dict["serialized_req"],
            request_dict["signatures"]
        )
