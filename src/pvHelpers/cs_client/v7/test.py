from pvHelpers.user import LocalUser
from pvHelpers.utils import params


class TestV7(object):
    @params(object, LocalUser, unicode)
    def expireDevice(self, user, device_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/devices/{}/expire".format(device_id), "PATCH", None
        )
        resp = self.patch(url, headers, raw_body, params={"user_id": user.user_id})
        resp.raise_for_status()
        return resp.json()
