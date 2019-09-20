from flanker import mime

import pvHelpers as H

from .prepared_message_base import PreparedMessageBase
from .prepared_message_helpers import (PreparedMessageError,
                                       PreparedMessageHelpers)


class PreparedMessageV1(PreparedMessageHelpers, PreparedMessageBase):
    """PV1 is complying prepared message for Email Entity PV1"""
    PROTOCOL_VERSION = H.PROTOCOL_VERSION.V1

    def __init__(self, sender, email, recipient):
        super(PreparedMessageV1, self).__init__(sender, email, recipient)

        if not isinstance(email, H.EmailV1):
            raise PreparedMessageError(u"PreparedMessageV1.__init__: email must be of type H.EmailV1")

        self._prepareAttachments(self.email.attachments)

        try:
            body_mime = mime.create.from_string(self.email.body.content)
        except mime.MimeError as e:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: flanker exception: {}".format(e))

        # This replacement due H.PROTOCOL_VERSION 1 body serialization which uses
        # block_ids of attachments for referencing dummy nodes, while locally we use
        # attachment hash for referencing so that attachment separation can be independent
        # of any encryption or server storage upload
        status, body_mime = H.EmailV1.replaceDummyReferences(body_mime, {H.HexEncode(H.Sha256Sum(att.content.content)): u",".join(att.content.block_ids) for att in self.email.attachments})
        if not status:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: Failed to replace dummy references")
        if self.recipient.user_id == self.sender.user_id:
            status, body_mime = H.EmailV1.setMIMEBcc(body_mime, self.email.bccs)
        else:
            if self.recipient.user_id in [bcc["user_id"] for bcc in self.email.bccs] or self.recipient.user_id not in [recip["user_id"] for recip in self.email.tos + self.email.ccs]:
                status, body_mime = H.EmailV1.setMIMEBcc(body_mime, [{"user_id": self.recipient.user_id, "display_name": self.recipient.display_name}])
            else:
                status, body_mime = H.EmailV1.setMIMEBcc(body_mime, [])

        if not status:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: Failed to modify Bccs")

        try:
            body = body_mime.to_string()
        except mime.MimeError as e:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: flanker exception: {}".format(e))

        self._prepareBody(body)

        status, signature = self._sign()
        if not status:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: Failed to sign content")

        self.private_metadata["sender"] = self.sender.user_id
        self.private_metadata["subject"] = self.email.subject
        self.private_metadata["signature"] = signature
        self.private_metadata["signing_key_version"] = self.sender.user_key.key_version

        self.private_metadata["tos"] = self.email.tos
        self.private_metadata["ccs"] = self.email.ccs

        encrypted_metadata = self._encrypt(H.jdumps(self.private_metadata), is_text=True)
        self.private_metadata = encrypted_metadata["ciphertext"]

    def _sign(self):
        status, canonical_msg_str = PreparedMessageV1.canonicalEncryptedString(self.uploads)
        if not status:
            H.g_log.error(u"PreparedMessageV1._sign: Failed to get canonical encrypted string")
            return False, None

        signature = H.b64enc(self.sender.user_key.signing_key.sign(H.utf8Encode(canonical_msg_str)))
        return True, signature

    @staticmethod
    def canonicalEncryptedString(blocks):
        msg = ""
        for block_id in sorted(blocks):
            block = blocks[block_id]
            if not isinstance(block, dict):
                H.g_log.error(u"PreparedMessageV1.canonicalEncryptedString: block must be of type dict")
                return False, None

            x = block.get("data")
            if not isinstance(x, unicode):
                H.g_log.error(u"PreparedMessageV1.canonicalEncryptedString: block data must be of type unicode")
                return False, None
            msg += x

        return True, msg
