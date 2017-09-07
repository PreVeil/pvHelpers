from .email_v2 import EmailV2
from .email_helpers import PROTOCOL_VERSION

class EmailV4(EmailV2):
    """Production version: Protocol version 4 is identical to protocol version 2"""
    protocol_version = PROTOCOL_VERSION.V4

    def __init__(self, *args, **kwargs):
        super(EmailV4, self).__init__(*args, **kwargs)
