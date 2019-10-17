from pvHelpers.user import LocalUser
from pvHelpers.utils import params


# For PreVeil privileged admins
class PVAdminV6(object):
    @params(object, LocalUser)
    def getStorageBackends(self, user):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/storage/backends", "GET", None
        )
        resp = self.get(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode)
    def setStorageBackend(self, user, org_id, backend):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/orgs/{}/storage_backend".format(org_id), "PATCH", None
        )
        resp = self.patch(url, headers, raw_body, params={ "name": backend })
        resp.raise_for_status()
        return resp.json()