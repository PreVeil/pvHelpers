import types

import pvHelpers as H

EXISTS = "exists"

class UserEventsV4(object):

    @H.params(object, H.LocalUser, unicode, {"approvers": [{"user_id": unicode, "key_version": {int, long}, "secret": unicode}]})
    def handleSetEDiscShardsEvent(self, user, event_id, request_data):
        return self.respondToUserEvent(user, event_id, request_data)

    @H.params(object, H.LocalUser, {types.NoneType, unicode}, unicode)
    def createUserEvent(self, user, member_id, payload):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/events", "POST", {
                "user_id" : member_id,
                "requester_id" : user.user_id,
                "requester_key_version" : user.user_key.key_version,
                "signature" : H.b64enc(user.user_key.signing_key.sign(H.utf8Encode(payload))),
                "payload" : payload
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @H.params(object, {H.UserDBNode, H.LocalUser}, int)
    def getUserEvents(self, user, last_rev_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/events", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            "user_id"      : user.user_id,
            "since_rev_id" : last_rev_id
        })
        resp.raise_for_status()
        return resp.json()

    @H.params(object, H.LocalUser, unicode, dict)
    def respondToUserEvent(self, user, event_id, response):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/events/{}".format(event_id), "PUT", {
                u"user_id" : user.user_id,
                u"request" : response
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
