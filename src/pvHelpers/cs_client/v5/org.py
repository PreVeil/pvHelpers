import types

from pvHelpers.request import UserRequest
from pvHelpers.user import LocalUser
from pvHelpers.utils import b64enc, merge_dicts, params, utf8_encode


class OrgV5(object):
    @params(object, LocalUser, unicode, {types.NoneType, unicode},
            {types.NoneType, bool}, {types.NoneType, unicode}, {types.NoneType, int}, {types.NoneType, int})
    def get_org_requests(self, user, org_id, status=None, hide_expired=None,
                         request_type=None, limit=None, offset=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/requests".format(org_id),
            "GET", None
        )
        hide_expired = str(hide_expired).lower() if hide_expired is not None else hide_expired
        request_type = str(request_type).lower() if request_type is not None else request_type
        resp = self.get(url, headers, params={
            "user_id": user.user_id,
            "status": status,
            "hide_expired": hide_expired,
            "request_type": request_type,
            "limit": limit,
            "offset": offset
        })
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode)
    def get_org_request_responses(self, user, org_id, request_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/requests/{}/responses".format(org_id, request_id),
            "GET", None
        )
        resp = self.get(url, headers)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode)
    def delete_org_request(self, user, org_id, request_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/requests/{}".format(org_id, request_id),
            "DELETE", None
        )
        resp = self.delete(url, headers, params={"user_id": user.user_id})
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, UserRequest, bool, dict)
    def respond_to_org_approval(self, user, org_id, request, response, metadata={}):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/requests/{}".format(org_id, request.request_id),
            "PUT", merge_dicts({
                "requester_user_id": request.user_id,
                "signature": b64enc(user.user_key.signing_key.sign(utf8_encode(request.serialized_req))),
                "approve": response,
            }, metadata)
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, unicode, {types.NoneType, unicode})
    def get_org_apg_info(self, user, org_id, group_id, group_version):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/groups/{}".format(org_id, group_id),
            "GET", None
        )
        resp = self.get(url, headers, params={"version": group_version})
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode)
    def get_org_whitelist(self, user, org_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/whitelist".format(org_id),
            "GET", None
        )
        resp = self.get(url, headers)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, {types.NoneType, list}, {types.NoneType, list})
    def add_to_org_whitelist(self, user, org_id, users, domains):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/whitelist/add".format(org_id),
            "PUT", {
                "users": users,
                "domains": domains
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, {types.NoneType, list}, {types.NoneType, list})
    def remove_from_org_whitelist(self, user, org_id, users, domains):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/whitelist/remove".format(org_id),
            "PUT", {
                "users": users,
                "domains": domains
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, bool)
    def toggle_org_whitelist(self, user, org_id, set_active):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/whitelist".format(org_id),
            "PATCH", {
                "set_active": set_active
            }
        )
        resp = self.patch(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, bool)
    def toggle_org_invite_email_send(self, user, org_id, no_download_email):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/orgs/{}/invite_email_type".format(org_id),
            "PATCH", {
                "no_download_email": no_download_email
            }
        )
        resp = self.patch(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
