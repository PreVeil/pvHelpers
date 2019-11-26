from pvHelpers.protos import Key as KeyBuffer
from pvHelpers.utils import b64enc

from .v0 import SignKeyV0, VerifyKeyV0


class VerifyKeyV1(VerifyKeyV0):
    protocol_version = 1

    def __init__(self, *args, **kwargs):
        super(VerifyKeyV1, self).__init__(*args, **kwargs)

    @property
    def key(self):
        return self.vk

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.vk)

    def serialize(self):
        b64 = b64enc(self.buffer.SerializeToString())
        return b64


class SignKeyV1(SignKeyV0):
    protocol_version = 1
    public_side_model = VerifyKeyV1

    def __init__(self, key=None):
        super(SignKeyV1, self).__init__(key)

    @property
    def key(self):
        return self.seed

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.seed
        )

    def serialize(self):
        b64 = b64enc(self.buffer.SerializeToString())
        return b64
