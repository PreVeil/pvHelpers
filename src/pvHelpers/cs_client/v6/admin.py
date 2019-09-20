
import pvHelpers as H

# For PreVeil privileged admins
class PVAdminV6(object):
    @H.params(object, H.LocalUser)
    def getStorageBackends(self, user):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/storage/backends", "GET", None
        )
        resp = self.get(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @H.params(object, H.LocalUser, unicode, unicode)
    def setStorageBackend(self, user, org_id, backend):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/orgs/{}/storage_backend".format(org_id), "PATCH", None
        )
        resp = self.patch(url, headers, raw_body, params={ "name": backend })
        resp.raise_for_status()
        return resp.json()
