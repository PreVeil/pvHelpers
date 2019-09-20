import types

import pvHelpers as H


class ApprovalsV5(object):
    @H.params(object, H.LocalUser, H.UserRequest, dict)
    def createH.UserRequest(self, user, request, metadata={}):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/requests", "POST", H.MergeDicts({
                "signature": request.signature,
                "request_payload" : request.serialized_req,
            }, metadata)
        )
        resp = self.post(url, headers, raw_body, params={"user_id": user.user_id})
        resp.raise_for_status()
        return resp.json()

    @H.params(object, H.LocalUser, {types.NoneType, unicode}, {types.NoneType, bool}, {types.NoneType, int}, {types.NoneType, int})
    def getH.UserRequests(self, user, status=None, hide_expired=None, limit=None, offset=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/requests",
            "GET", None
        )
        hide_expired = str(hide_expired).lower() if hide_expired != None else hide_expired
        resp = self.get(url, headers, params={"user_id": user.user_id, "status": status, "hide_expired": hide_expired, "limit": limit, "offset": offset})
        resp.raise_for_status()
        return resp.json()

    @H.params(object, H.LocalUser, unicode)
    def getH.UserRequestResponses(self, user, request_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/requests/{}/responses".format(request_id),
            "GET", None
        )
        resp = self.get(url, headers, params={"user_id": user.user_id})
        resp.raise_for_status()
        return resp.json()

    @H.params(object, H.LocalUser, unicode)
    def deleteH.UserRequest(self, user, request_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/requests/{}".format(request_id),
            "DELETE", None
        )
        resp = self.delete(url, headers, params={"user_id": user.user_id})
        resp.raise_for_status()
        return resp.json()

    @H.params(object, H.LocalUser, {unicode, types.NoneType}, {unicode, types.NoneType}, {bool, types.NoneType}, {types.NoneType, int}, {types.NoneType, int})
    def getUserApprovals(self, user, status=None, response=None, hide_expired=None, offset=None, limit=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/approvals",
            "GET", None
        )
        hide_expired = str(hide_expired).lower() if hide_expired != None else hide_expired
        resp = self.get(url, headers, params={
            "user_id": user.user_id, "status": status, "response": response,
            "hide_expired": hide_expired, "limit": limit, "offset": offset
        })
        resp.raise_for_status()
        return resp.json()

    @H.params(object, H.LocalUser, H.UserRequest, bool)
    def respondToUserApproval(self, user, request, response):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/approvals/{}".format(request.request_id),
            "PUT", {
                "user_id": user.user_id,
                "requester_user_id": request.user_id,
                "signature": H.b64enc(user.user_key.signing_key.sign(H.utf8Encode(request.serialized_req))),
                "approve": response
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
