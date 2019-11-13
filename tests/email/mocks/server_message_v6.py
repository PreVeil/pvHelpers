from random import randint

from pvHelpers.crypto import PVKeyFactory
from pvHelpers.utils import MergeDicts, randUnicode

from . import MockPrivateMetadataV5, MockServerMessageV5, recipient


def make_group_recipients(counts=2):
    groups = {}
    for _ in range(counts):
        alias = randUnicode(5)
        members = [recipient() for _ in range(randint(1, 4))]
        groups[alias] = {"alias": "{}@alias.test.preveil.com".format(alias), "users": members}
    return groups


# TODO: mock attachments
class MockPrivateMetadataV6(MockPrivateMetadataV5):
    protocol_version = 6

    def __init__(self,
                 tos_groups=make_group_recipients(randint(1, 4)).values(),
                 ccs_groups=make_group_recipients(randint(1, 4)).values(),
                 subject=None,
                 sender=None,
                 user_key=None,
                 symm_key=PVKeyFactory.newSymmKey()):
        super(MockPrivateMetadataV6, self).__init__(
            subject,
            sender,
            user_key,
            symm_key
        )

        self.tos_groups = tos_groups
        self.ccs_groups = ccs_groups

    def toDict(self):
        shares = super(MockPrivateMetadataV6, self).toDict()
        return MergeDicts({
            "ccs_groups": self.ccs_groups,
            "tos_groups": self.tos_groups
        }, shares)


class MockServerMessageV6(MockServerMessageV5):
    protocol_version = 6

    def __init__(self,
                 private_metadata,
                 signature,
                 sender_key_version,
                 recipient_key_version,
                 wrapped_key,
                 wrapped_recipients,
                 wrapped_bccs=None):
        super(MockServerMessageV6, self).__init__(
            private_metadata,
            signature,
            sender_key_version,
            recipient_key_version,
            wrapped_key,
            wrapped_recipients,
            wrapped_bccs)