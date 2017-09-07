from .email_v1 import EmailV1
from .email_helpers import PROTOCOL_VERSION

class EmailV3(EmailV1):
    """Testing version: Protocol version 3 is identical to protocol version 1"""
    protocol_version = PROTOCOL_VERSION.V3

    def __init__(self, *args, **kwargs):
        super(EmailV3, self).__init__(*args, **kwargs)
