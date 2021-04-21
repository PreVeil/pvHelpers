from .email_v4 import EmailV4
from .email_helpers import PROTOCOL_VERSION


class EmailV7(EmailV4):
    "Production version: Email version 7 is identical to Email version 4 and is included to correspond to prepared_message v7 (supports aliasing for email gateway)"

    protocol_version = PROTOCOL_VERSION.V7

    def __init__(self, *args, **kwargs):
        super(EmailV7, self).__init__(*args, **kwargs)