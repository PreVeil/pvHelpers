import pvHelpers as H

from .prepared_message_v2 import PreparedMessageV2
from .prepared_message_v3 import PreparedMessageV3


class PreparedMessageV4(PreparedMessageV2):
    """PV4 is identical to PV2 as for email entity and identical to PV3 as for signiture"""
    PROTOCOL_VERSION = H.PROTOCOL_VERSION.V4

    def __init__(self, sender, email, recipient):
        super(PreparedMessageV4, self).__init__(sender, email, recipient)

    def _sign(self):
        canonical_msg_str = PreparedMessageV4.canonicalEncryptedString(
            self.uploads)
        signature = H.b64enc(self.sender.user_key.signing_key.sign(
            H.utf8Encode(canonical_msg_str)))
        return True, signature

    @staticmethod
    def canonicalEncryptedString(blocks):
        return PreparedMessageV3.canonicalEncryptedString(blocks)
