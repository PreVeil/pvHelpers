import pvHelpers as H


# For PreVeil privileged admins
class PVAdminV4(object):
    @H.params(object, H.LocalUser, object)
    def deleteUser(self, user, params):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users", "DELETE", None
        )
        resp = self.delete(url, headers, raw_body, params=params)
        resp.raise_for_status()
        return resp.json()

    @H.params(object, H.LocalUser, bool, {int, long}, {int, long})
    def getUsersList(self, user, show_unclaimed, limit, offset):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/list", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            "show_unclaimed" : show_unclaimed,
            "offset" : offset,
            "limit" : limit
        })
        resp.raise_for_status()
        return resp.json()
