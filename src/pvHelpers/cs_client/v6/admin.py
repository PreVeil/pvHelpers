from pvHelpers.user import LocalUser
from pvHelpers.utils import params


# For PreVeil privileged admins
class PVAdminV6(object):
    @params(object, LocalUser)
    def get_storage_backends(self, user):
        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/storage/backends", "GET", None
        )
        resp = self.get(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode)
    def set_storage_backend(self, user, org_id, backend):
        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/users/orgs/{}/storage_backend".format(org_id), "PATCH", None
        )
        resp = self.patch(url, headers, raw_body, params={"name": backend})
        resp.raise_for_status()
        return resp.json()
