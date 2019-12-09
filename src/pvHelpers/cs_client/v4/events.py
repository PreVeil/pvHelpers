import types

from pvHelpers.user import LocalUser
from pvHelpers.utils import b64enc, params, utf8_encode


EXISTS = "exists"


class UserEventsV4(object):
    @params(object, LocalUser, {types.NoneType, unicode}, unicode)
    def create_user_event(self, user, member_id, payload):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/events", "POST", {
                "user_id": member_id,
                "requester_id": user.user_id,
                "requester_key_version": user.user_key.key_version,
                "signature": b64enc(user.user_key.signing_key.sign(utf8_encode(payload))),
                "payload": payload
            }
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, int)
    def get_user_events(self, user, last_rev_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/events", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            "user_id": user.user_id,
            "since_rev_id": last_rev_id
        })
        resp.raise_for_status()
        return resp.json()

    @params(object, LocalUser, unicode, dict)
    def respond_to_user_event(self, user, event_id, response):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/users/events/{}".format(event_id), "PUT", {
                u"user_id": user.user_id,
                u"request": response
            }
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
