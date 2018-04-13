from .sign_key_v0 import SignKeyV0, VerifyKeyV0
from ..utils import KeyBuffer

class VerifyKeyV1(VerifyKeyV0):
    protocol_version = 1

    def __init__(self, *args, **kwargs):
        super(VerifyKeyV1, self).__init__(*args, **kwargs)

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.vk
        )


class SignKeyV1(SignKeyV0):
    protocol_version = 1
    public_side_model = VerifyKeyV1

    def __init__(self, seed=None):
        super(SignKeyV1, self).__init__(seed)

    @property
    def buffer(self):
        return KeyBuffer(
            protocol_version=self.protocol_version,
            key=self.seed
        )

    def __eq__(self, other):
        if other.protocol_version == SignKeyV0.protocol_version:
            return self._signer.seed == other.seed

        return self.protocol_version == other.protocol_version and \
            self._signer.seed == other.seed
