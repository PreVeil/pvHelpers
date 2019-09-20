from pvHelpers.user import LocalDevice
from pvHelpers.utils import params


class DeviceRequest(object):
    @classmethod
    @params(object, unicode, LocalDevice)
    def newForRecovery(cls, user_id, device):
        timestamp = datetime.datetime.utcnow()
        expiration = timestamp + datetime.timedelta(days=7)
        return cls(device, jdumps({
            "user_id": user_id,
            "type": "add_device",
            "timestamp": timestamp.isoformat(),
            "expiration": expiration.isoformat(),
            "data": device.toDict()
        }), [])

    @classmethod
    @params(object, unicode, LocalDevice)
    def newForTransfer(cls, user_id, device):
        return cls(device, jdumps(device.toDict()), [])

    def __init__(self, device, serialized_req, signatures):
        self.device = device
        self.serialized_req = serialized_req
        self.signatures = signatures

    def toDB(self):
        return {
            "device": self.device.toDB(),
            "serialized_req": self.serialized_req,
            "signatures": self.signatures
        }

    @classmethod
    def fromDB(cls, request_dict):
        return cls(
            LocalDevice.fromDB(request_dict["device"]),
            request_dict["serialized_req"],
            request_dict["signatures"]
        )
