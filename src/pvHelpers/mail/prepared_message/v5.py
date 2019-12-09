from pvHelpers.crypto import sha_256_sum
from pvHelpers.mail.email import EmailRecipients, PROTOCOL_VERSION
from pvHelpers.utils import b64enc, jdumps, utf8_encode

from .base import PreparedMessageBase
from .helpers import PreparedMessageError, PreparedMessageHelpers


class PreparedMessageV5(PreparedMessageHelpers, PreparedMessageBase):
    protocol_version = PROTOCOL_VERSION.V5

    def __init__(self, sender, email, recipients):
        self.signature = None
        self._recipients_for_server = None
        self._bccs = None
        self.sealed_opaque_key = None
        self.recipients = recipients
        super(PreparedMessageV5, self).__init__(sender, email)

        self.sealed_opaque_key = self.wrapped_key_for(
            self.opaque_key, self.sender)
        self._prepare_attachments(self.email.attachments, PROTOCOL_VERSION.V5)
        self._prepare_body(self.email.body.content, PROTOCOL_VERSION.V5)

        self.private_metadata["body"] = self.body
        self.private_metadata["attachments"] = self.attachments
        self.private_metadata["subject"] = self.email.subject
        self.private_metadata["sender"] = self.sender.user_id
        self.private_metadata["tos"] = self._prepare_recipient_list(EmailRecipients.Tos)
        self.private_metadata["ccs"] = self._prepare_recipient_list(EmailRecipients.Ccs)
        self._bccs = self._prepare_recipient_list(EmailRecipients.Bccs)
        self._recipients_for_server = list(self.private_metadata["tos"] + self.private_metadata["ccs"])
        self.private_metadata["other_headers"] = self.email.other_headers

        # sign the sha256(private_metadata)
        json_private_metadata = jdumps(self.private_metadata)
        utf8_encode_pvm = utf8_encode(json_private_metadata)
        pvm_hash = sha_256_sum(utf8_encode_pvm)
        self.signature = b64enc(self.sender.user_key.signing_key.sign(pvm_hash))

        # encrypt the private_metadata using the opaque_key
        encrypted_metadata = self._encrypt(utf8_encode_pvm)
        self.private_metadata = encrypted_metadata["ciphertext"]  # base64 encoded

    def _prepare_recipient_list(self, recip_type):
        recips = None
        if recip_type == EmailRecipients.Tos:
            recips = self.email.tos
        elif recip_type == EmailRecipients.Ccs:
            recips = self.email.ccs
        elif recip_type == EmailRecipients.Bccs:
            recips = self.email.bccs
        else:
            raise PreparedMessageError("PreparedMessageV5: invalid email recipient type {}".format(recip_type))

        out = []
        for r in recips:
            user_id = r["user_id"]
            recip = self.recipients.get(user_id)
            if user_id not in self.recipients:
                key_version = None
                wrapped_key = None
            else:
                key_version = recip.public_user_key.key_version if recip.is_claimed() else None
                wrapped_key = self.wrapped_key_for(self.opaque_key, recip) if recip.is_claimed() else None
            entry = {"user_id": user_id, "key_version": key_version,
                     "wrapped_key": wrapped_key}
            out.append(entry)
        return out

    def to_dict(self):
        return {
            "message": self._message(),
            "recipients": self._recipients_for_server,
            "bccs": self._bccs,
        }

    def _message(self):
        return {
            "protocol_version": self.protocol_version,
            "message_id": self.email.message_id,
            "in_reply_to": self.email.in_reply_to,
            "references": self.email.references,
            "private_metadata": self.private_metadata,
            "signature": self.signature,
            "wrapped_key": self.sealed_opaque_key,
            "block_ids":
                self.body["block_ids"] + reduce(lambda acc, item: acc + item["block_ids"], self.attachments, [])
        }
