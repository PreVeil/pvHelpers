from pvHelpers.crypto.user_key import UserKeyBase
from pvHelpers.user import LocalDevice
from pvHelpers.utils import params


class PublicV5(object):
    @params(object, unicode, unicode, UserKeyBase, unicode, unicode, LocalDevice)
    def claim_user(self, user_id, secret, user_key, wrapped_log_viewer_private_key, serialized_log_viewer_key, device):
        url, raw_body, headers = self.prepare_public_request(
            u"/users", "PUT", {
                "user_id": user_id,
                "secret": secret,
                "public_keys": {
                    u"public_key": user_key.public_user_key.serialize(),
                    u"log_viewer_key": serialized_log_viewer_key
                },
                "wrapped_keys": {
                    u"wrapped_log_viewer_private_key": wrapped_log_viewer_private_key
                },
                "device": {
                    "device_id": device.id,
                    "platform": device.platform,
                    "public_key": device.key.public_user_key.serialize(),
                    "metadata": device.metadata,
                    "device_name": device.name
                }
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
