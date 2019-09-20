import types

import pvHelpers as H


class DeviceV5(object):
    @params(object, H.LocalUser, H.UserKeyBase)
    def refreshDeviceKey(self, user, new_device_key):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/devices/keys/{}".format(user.device.id), "PUT", {
                "user_id": user.user_id,
                "public_key" : new_device_key.public_user_key.serialize(),
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, H.LocalUser, dict, unicode, {types.NoneType, unicode})
    def editDeviceInfo(self, user, new_metadata, new_name, device_id=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/devices/keys/{}".format(user.device.id if device_id is None else device_id),
            "PATCH", {
                "user_id": user.user_id,
                "device_name" : new_name,
                "metadata": new_metadata
            }
        )
        resp = self.patch(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, H.LocalUser, unicode, {types.NoneType, unicode})
    def deleteUserDevice(self, user, device_id, for_user_id=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/devices/keys/{}".format(device_id),
            "DELETE", {"user_id": user.user_id if for_user_id is None else for_user_id}
        )
        resp = self.delete(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, H.LocalUser, {types.NoneType, unicode})
    def getUserDevices(self, user, for_user=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/devices/keys",
            "GET", None
        )
        resp = self.get(url, headers, params={"user_id": user.user_id if for_user is None else for_user})
        resp.raise_for_status()
        return resp.json()

    @params(object, H.LocalUser, unicode, {types.NoneType, unicode})
    def getUserDevice(self, user, device_id, for_user=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/users/devices/keys/{}".format(device_id),
            "GET", None
        )
        resp = self.get(url, headers, params={"user_id": user.user_id if for_user is None else for_user})
        resp.raise_for_status()
        return resp.json()

    # add a Device Key for an existing account
    # @params(object, H.LocalUser, LocalDevice, [{"user_id": unicode, "user_key_version": {int, long}, "signature": unicode}])
    def addDevice(self, user, device, signatures=[]):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/users/devices/keys",
            "POST", {
                "user_id": user.user_id,
                "serialized_request": device,
                "approver_signatures": signatures
            }, ignore_device_sign=True
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    # add a Device Key for an existing account
    @params(object, H.LocalUser, H.LocalDevice)
    def addDeviceLegacy(self, user, device):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/users/devices/keys",
            "POST", {
                "user_id": user.user_id,
                "device": device.toDict()
            }, ignore_device_sign=True
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, H.LocalUser, unicode, {types.NoneType, unicode})
    def lockUserDevice(self, user, device_id, for_user=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/devices/keys/{}/lock".format(device_id),
            "PATCH", {
                "user_id": user.user_id if for_user is None else for_user
            }
        )
        resp = self.patch(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, H.LocalUser, unicode, {types.NoneType, unicode})
    def unlockUserDevice(self, user, device_id, for_user=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/devices/keys/{}/unlock".format(device_id),
            "PATCH", {
                "user_id": user.user_id if for_user is None else for_user
            }
        )
        resp = self.patch(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
