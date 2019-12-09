from pvHelpers.user import LocalUser
from pvHelpers.utils import params


# For PreVeil privileged admins
class PVAdminV4(object):
    @params(object, LocalUser, object)
    def delete_user(self, user, params):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users", "DELETE", None
        )
        resp = self.delete(url, headers, raw_body, params=params)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, bool, {int, long}, {int, long})
    def get_users_list(self, user, show_unclaimed, limit, offset):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/list", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            "show_unclaimed": show_unclaimed,
            "offset": offset,
            "limit": limit
        })
        resp.raise_for_status()
        return resp.json()
