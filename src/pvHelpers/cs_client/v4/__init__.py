from pvHelpers.http_client import HTTPClient
from pvHelpers.utils import b64enc, jdumps, utf8_encode

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


class APIClientV4(PublicV4, UserV4, MailV4, MailboxV4, OrgV4, PVAdminV4, UserEventsV4, GroupV4, StorageV4, TestV4, HTTPClient):
    __api_version__ = 4

    def _prepare_public_request(self, resource, method, body):
        url = self.url + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = jdumps(body)

        headers = {
            "content-type" : "application/json",
            "accept-version" : str(self.accept_version())
        }
        encoded_raw_body = utf8_encode(raw_body)
        return url, encoded_raw_body, headers

    def _prepare_signed_request(self, signer, resource, method, body):
        url = self.url + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = jdumps(body)

        canonical_request = u"{};{};{}".format(resource, method, raw_body)

        encoded_user_id = utf8_encode(signer.user_id)
        user_key_version, user_signature = signer.sign_with_user_key(utf8_encode(canonical_request))
        headers = {
            "content-type": "application/json",
            "x-user-id": encoded_user_id,
            "x-signature": b64enc(user_signature),
            "accept-version" :  str(self.accept_version())
        }
        encoded_raw_body = utf8_encode(raw_body)

        return url, encoded_raw_body, headers