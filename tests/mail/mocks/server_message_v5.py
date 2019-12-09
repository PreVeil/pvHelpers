from random import randint

from pvHelpers.crypto import PVKeyFactory, sha_256_sum
from pvHelpers.utils import b64enc, jdumps, merge_dicts, rand_unicode, utf8_encode

from . import MockServerMessageBase, recipient


# TODO: mock attachments
class MockPrivateMetadataV5(object):
    protocol_version = 5

    def __init__(self,
                 subject=None,
                 sender=None,
                 user_key=None,
                 symm_key=PVKeyFactory.new_symm_key()):
        self.subject = subject if subject else rand_unicode(5)
        self.sender = sender if sender else rand_unicode(5)
        self.tos = [recipient() for _ in range(3)]
        self.ccs = [recipient() for _ in range(3)]
        self.body = {
            "block_ids": [rand_unicode(5) for _ in range(3)],
            "snippet": rand_unicode(5),
            "size": randint(0, 100),
        }
        self.attachments = []
        self.other_headers = {}
        self.symm_key = symm_key
        self.user_key = user_key if user_key else PVKeyFactory.new_user_key(
            key_version=0)

    def to_dict(self):
        return {
            "subject": self.subject,
            "sender": self.sender,
            "tos": self.tos,
            "ccs": self.ccs,
            "body": self.body,
            "attachments": self.attachments,
            "other_headers": self.other_headers
        }

    def sign_and_encrypt(self):
        json_private_metadata = jdumps(self.to_dict())
        utf8_encode_pvm = utf8_encode(json_private_metadata)
        pvm_hash = sha_256_sum(utf8_encode_pvm)
        return b64enc(self.user_key.signing_key.sign(
            pvm_hash)), b64enc(self.symm_key.encrypt(utf8_encode_pvm))


class MockServerMessageV5(MockServerMessageBase):
    protocol_version = 5

    def __init__(self, private_metadata, signature, sender_key_version, recipient_key_version,
                 wrapped_key, wrapped_recipients, wrapped_bccs=None):
        self.signature = signature
        self.sender_key_version = sender_key_version
        self.recipient_key_version = recipient_key_version
        self.wrapped_key = wrapped_key
        self.wrapped_recipients = wrapped_recipients
        self.wrapped_bccs = wrapped_bccs
        super(MockServerMessageV5, self).__init__(self.protocol_version, private_metadata)

    def to_dict(self):
        commons = super(MockServerMessageV5, self).to_dict()
        specifics = {
            "signature": self.signature,
            "sender_key_version": self.sender_key_version,
            "recipient_key_version": self.recipient_key_version,
            "wrapped_key": self.wrapped_key,
            "wrapped_recipients": self.wrapped_recipients,
            "wrapped_bccs": self.wrapped_bccs
        }
        return merge_dicts(commons, specifics)
