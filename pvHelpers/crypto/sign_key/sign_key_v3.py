from .sign_key_v0 import SignKeyV0, VerifyKeyV0
from ..utils import KeyBuffer, b64enc

class VerifyKeyV3(VerifyKeyV0):
    protocol_version = 3

    def __init__(self):
        super(VerifyKeyV3, self).__init__()


class SignKeyV3(SignKeyV0):
    protocol_version = 3
    public_side_model = VerifyKeyV3

    def __init__(self):
        super(SignKeyV3, self).__init__(seed)
