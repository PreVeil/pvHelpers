from pvHelpers.crypto import Sha256Sum
from pvHelpers.logger import g_log
from pvHelpers.mail.email import EmailRecipients, PROTOCOL_VERSION
from pvHelpers.user import UserGroup
from pvHelpers.utils import b64enc, CaseInsensitiveDict, jdumps, utf8Encode

from .base import PreparedMessageBase
from .helpers import PreparedMessageError, PreparedMessageHelpers


class PreparedMessageV6(PreparedMessageHelpers, PreparedMessageBase):
    protocol_version = PROTOCOL_VERSION.V6

    def __init__(self, sender, email, recipients):
        self.signature = None
        self.sealed_opaque_key = None
        self.recipients = recipients
        super(PreparedMessageV6, self).__init__(sender, email)

        self.sealed_opaque_key = self.wrapped_key_for(
            self.opaque_key, self.sender)
        self._prepare_attachments(self.email.attachments, PROTOCOL_VERSION.V6)
        self._prepare_body(self.email.body.content, PROTOCOL_VERSION.V6)

        self.private_metadata["body"] = self.body
        self.private_metadata["attachments"] = self.attachments
        self.private_metadata["subject"] = self.email.subject
        self.private_metadata["sender"] = self.sender.user_id

        tos, tos_groups = self._prepare_recipient_list(EmailRecipients.Tos)
        self.private_metadata["tos"] = tos
        self.private_metadata["tos_groups"] = tos_groups
        ccs, ccs_groups = self._prepare_recipient_list(EmailRecipients.Ccs)
        self.private_metadata["ccs"] = ccs
        self.private_metadata["ccs_groups"] = ccs_groups

        self.private_metadata["other_headers"] = self.email.other_headers

        # sign the sha256(private_metadata)
        json_private_metadata = jdumps(self.private_metadata)
        utf8_encode_pvm = utf8Encode(json_private_metadata)
        pvm_hash = Sha256Sum(utf8_encode_pvm)
        self.signature = b64enc(
            self.sender.user_key.signing_key.sign(pvm_hash))

        # encrypt the private_metadata using the opaque_key
        encrypted_metadata = self._encrypt(utf8_encode_pvm)
        # base64 encoded
        self.private_metadata = encrypted_metadata["ciphertext"]

    def _flatten_recipients(self):
        """
            return
                :all_other_recipients: which includes all tos, ccs, and members of tos_group and ccs_group.
                :all_bcc_recipients: which includes only bccs and members of bccs_group.
        """
        all_other_recipients = CaseInsensitiveDict()
        all_bcc_recipients = CaseInsensitiveDict()
        bcc_ids = map(lambda u: u["user_id"], self.email.bccs)
        all_ids = map(lambda u: u["user_id"], self.email.bccs + self.email.tos + self.email.ccs)

        for id_ in all_ids:
            recip = self.recipients.get(id_, None)

            if id_ in bcc_ids:
                insert_dict = all_bcc_recipients
            else:
                insert_dict = all_other_recipients

            if isinstance(recip, UserGroup):
                # add all group members
                for gm in recip.members:
                    if gm not in insert_dict:
                        # validate that the group member exists
                        if gm not in self.recipients:
                            g_log.error(
                                "member={} of group_alias={} is a no longer a valid user".format(gm, recip.address))
                            continue

                        gm_user = self.recipients.get(gm)
                        insert_dict[gm] = {
                            "user_id": gm,
                            "key_version": gm_user.public_user_key.key_version,
                            "wrapped_key": self.wrapped_key_for(self.opaque_key, gm_user)
                        }
                continue

            # add individual recip
            if id_ not in insert_dict:
                key_version, wrapped_key = None, None
                if recip and recip.is_claimed():
                    key_version = recip.public_user_key.key_version
                    wrapped_key = self.wrapped_key_for(self.opaque_key, recip)

                insert_dict[id_] = {
                    "user_id": id_,
                    "key_version": key_version,
                    "wrapped_key": wrapped_key
                }

        return all_other_recipients.values(), all_bcc_recipients.values()

    def _validate_group_members(self, group, include_wrapped_key=False):
        # workaround: https://preveil.atlassian.net/browse/BUG-680
        o = []
        for m in group.members:
            if m in self.recipients:
                o.append(
                    {
                        "user_id": m,
                        "key_version": self.recipients.get(m).public_user_key.key_version
                    }
                )
            else:
                g_log.error(
                    "member={} of group_alias={} is a no longer a valid user".format(m, group.address))
        return o

    def _prepare_recipient_list(self, recip_type):
        """
            return
                tos: [{"user_id": string, "key_version": int/None}*],
                tos_groups [ {"alias": string, "users": [{"user_id": string, "key_version": int}] }*]:
                or
                ccs,
                ccs_groups
        """
        recips = None
        if recip_type == EmailRecipients.Tos:
            recips = self.email.tos
        elif recip_type == EmailRecipients.Ccs:
            recips = self.email.ccs
        else:
            raise PreparedMessageError(
                "PreparedMessageV6: invalid email recipient type {}".format(recip_type))

        individual_recips, groups = [], []
        for r in recips:
            user_id = r["user_id"]
            key_version = None
            if user_id in self.recipients:
                recip = self.recipients.get(user_id)
                if isinstance(recip, UserGroup):
                    # right now, all group member must be a claimed account
                    groups.append(
                        {
                            "alias": recip.address,
                            "users": self._validate_group_members(recip)
                        }
                    )
                    continue

                if recip.is_claimed():
                    key_version = recip.public_user_key.key_version

            individual_recips.append({"user_id": user_id, "key_version": key_version})

        return individual_recips, groups

    def to_dict(self):
        recipients, bccs = self._flatten_recipients()
        return {
            "message": self._message(),
            "recipients": recipients,
            "bccs": bccs,
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
