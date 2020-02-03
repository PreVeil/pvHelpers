from pvHelpers.utils import jdumps


class Device(object):
    def list_user_devices(self, user_id, for_user=None):
        resp = self.put(
            u"{}/user/{}/device/list".format(self.url, user_id),
            raw_body=jdumps({"for_user": for_user})
        )
        resp.raise_for_status()
        return resp.json()

    def patch_user_device(self, user_id, device_id, new_name):
        resp = self.put(
            u"{}/user/{}/device/{}/patch".format(self.url, user_id, device_id),
            raw_body=jdumps({"name": new_name})
        )
        resp.raise_for_status()
        return resp.json()

    def lock_user_device(self, user_id, device_id, for_user=None):
        resp = self.put(
            u"{}/user/{}/device/{}/lock".format(self.url, user_id, device_id),
            raw_body=jdumps({"for_user": for_user})
        )
        resp.raise_for_status()
        return resp.json()

    def unlock_user_device(self, user_id, device_id, for_user=None):
        resp = self.put(
            u"{}/user/{}/device/{}/unlock".format(self.url, user_id, device_id),
            raw_body=jdumps({"for_user": for_user})
        )
        resp.raise_for_status()
        return resp.json()

    def refresh_user_device_key(self, user_id):
        resp = self.put(
            u"{}/user/{}/device/refresh".format(self.url, user_id))

        resp.raise_for_status()
        return resp.json()
