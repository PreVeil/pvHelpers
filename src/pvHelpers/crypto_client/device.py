from pvHelpers.utils import jdumps


class Device(object):
    def listUserDevices(self, user_id, for_user=None):
        resp = self.put(
            u"{}/user/{}/device/list".format(self.url, user_id),
            headers=self.__headers__,
            raw_body=jdumps({"for_user": for_user})
        )
        resp.raise_for_status()
        return resp.json()

    def patchUserDevice(self, user_id, device_id, new_name):
        resp = self.put(
            u"{}/user/{}/device/{}/patch".format(self.url, user_id, device_id),
            headers=self.__headers__,
            raw_body=jdumps({"name": new_name})
        )
        resp.raise_for_status()
        return resp.json()

    def lockUserDevice(self, user_id, device_id, for_user=None):
        resp = self.put(
            u"{}/user/{}/device/{}/lock".format(self.url, user_id, device_id),
            headers=self.__headers__,
            raw_body=jdumps({"for_user": for_user})
        )
        resp.raise_for_status()
        return resp.json()

    def unlockUserDevice(self, user_id, device_id, for_user=None):
        resp = self.put(
            u"{}/user/{}/device/{}/unlock".format(self.url, user_id, device_id),
            headers=self.__headers__,
            raw_body=jdumps({"for_user": for_user})
        )
        resp.raise_for_status()
        return resp.json()
