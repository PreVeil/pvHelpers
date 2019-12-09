from pvHelpers.mail.email import PROTOCOL_VERSION
from pvHelpers.utils import b64enc, utf8_encode

from .v2 import PreparedMessageV2
from .v3 import PreparedMessageV3


class PreparedMessageV4(PreparedMessageV2):
    """PV4 is identical to PV2 as for email entity and identical to PV3 as for signiture"""
    PROTOCOL_VERSION = PROTOCOL_VERSION.V4

    def __init__(self, sender, email, recipient):
        super(PreparedMessageV4, self).__init__(sender, email, recipient)

    def _sign(self):
        canonical_msg_str = PreparedMessageV4.canonical_encrypted_string(
            self.uploads)
        signature = b64enc(self.sender.user_key.signing_key.sign(
            utf8_encode(canonical_msg_str)))
        return True, signature

    @staticmethod
    def canonical_encrypted_string(blocks):
        return PreparedMessageV3.canonical_encrypted_string(blocks)
