from pvHelpers.utils import b64enc, jdumps, utf8Encode

from ..v4 import APIClientV4
from .approvals import ApprovalsV5
from .device import DeviceV5
from .ediscovery import EDiscoveryV5
from .mail import MailV5
from .org import OrgV5
from .public import PublicV5
from .user import UserV5


class APIClientV5(UserV5, OrgV5, MailV5, EDiscoveryV5, ApprovalsV5, DeviceV5, PublicV5, APIClientV4):
    __api_version__ = 5

    def __init__(self, backend):
        super(APIClientV5, self).__init__(backend)

    def _prepareSignedRequest(self, signer, resource, method, body, ignore_device_sign=False, export=None):
        if not ignore_device_sign and not signer.has_device_key():
            raise MissingDeviceKey("V5 requires device key")
        url = self.url + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = jdumps(body)

        canonical_request = u"{};{};{}".format(resource, method, raw_body)
        if not ignore_device_sign:
            device_key_version, device_signature = signer.sign_with_device_key(utf8Encode(canonical_request))
            user_key_version, user_signature = signer.sign_with_user_key(device_signature)
        else:
            user_key_version, user_signature = signer.sign_with_user_key(utf8Encode(canonical_request))
        encoded_user_id = utf8Encode(signer.user_id)
        export_id, member_id = None, None
        if export:
            export_id, member_id = export
            member_id = utf8Encode(member_id)
        headers = {
            "content-type" : "application/json",
            "x-user-key-version": str(user_key_version),
            "x-user-id"    : encoded_user_id,
            "x-user-signature": b64enc(user_signature),
            "accept-version" : str(self.accept_version()),
            "x-device-signature"  : None if ignore_device_sign else b64enc(device_signature),
            "x-device-id": None if ignore_device_sign else signer.device.id,
            "x-device-key-version": None if ignore_device_sign else str(device_key_version),
            "x-data-export-id": export_id,
            "x-for-user-id": member_id,
        }
        encoded_raw_body = utf8Encode(raw_body)
        return url, encoded_raw_body, headers
