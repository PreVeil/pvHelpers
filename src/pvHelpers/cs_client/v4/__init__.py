import pvHelpers as H

from .admin import PVAdminV4
from .events import UserEventsV4
from .group import GroupV4
from .mail import MailV4
from .mailbox import MailboxV4
from .org import OrgV4
from .public import PublicV4
from .storage import StorageV4
from .test import TestV4
from .user import UserV4


class APIClientV4(H.APIClient, PublicV4, UserV4, MailV4, MailboxV4, OrgV4, PVAdminV4, UserEventsV4, GroupV4, StorageV4, TestV4):
    __api_version__ = u"v4"

    def __init__(self, backend):
        super(APIClientV4, self).__init__(backend)

    def preparePublicRequest(self, resource, method, body):
        url = self.backend + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = H.jdumps(body)

        headers = {
            "content-type" : "application/json",
            "accept-version" : self.__api_version__
        }
        encoded_raw_body = H.utf8Encode(raw_body)
        return url, encoded_raw_body, headers

    def prepareSignedRequest(self, signer, resource, method, body):
        url = self.backend + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = H.jdumps(body)

        canonical_request = u"{};{};{}".format(resource, method, raw_body)

        encoded_user_id = H.utf8Encode(signer.user_id)
        user_key_version, user_signature = signer.signWithUserKey(H.utf8Encode(canonical_request))
        headers = {
            "content-type" : "application/json",
            "x-user-id"    : encoded_user_id,
            "x-signature": H.b64enc(user_signature),
            "accept-version" : self.__api_version__,
        }
        encoded_raw_body = H.utf8Encode(raw_body)

        return url, encoded_raw_body, headers
