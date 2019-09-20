import types

import pvHelpers as H


class PublicV4(object):
    @H.params(object, unicode, unicode, H.UserKeyBase, unicode, unicode, H.LocalDevice)
    def claimUser(self, user_id, secret, user_key, wrapped_log_viewer_private_key, serialized_log_viewer_key, device):
        url, raw_body, headers = self.preparePublicRequest(
            u"/users", "PUT", {
                "user_id": user_id,
                "secret": secret,
                "public_keys" : {
                    u"public_key" : user_key.public_user_key.serialize(),
                    u"log_viewer_key" : serialized_log_viewer_key
                },
                "wrapped_keys": {
                    u"wrapped_log_viewer_private_key" : wrapped_log_viewer_private_key
                }
            }
        )

        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()


    @H.params(object, unicode, unicode)
    def createUser(self, user_id, name):
        url, raw_body, headers = self.preparePublicRequest(
            u"/users", "POST", {
                "user_id": user_id,
                "display_name": name
            }
        )

        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()


    def ping(self):
        url, raw_body, headers = self.preparePublicRequest(
            u"/ping", "GET", None
        )
        resp = self.get(url, headers, raw_body, timeout=1)
        resp.raise_for_status()


    @H.params(object, unicode, unicode)
    def fetchApprovalGroupWithSecret(self, user_id, secret):
        url, raw_body, headers = self.preparePublicRequest(
            u"/users/approvers/info", "GET", None
        )

        resp = self.get(url, headers, raw_body, params={"user_id": user_id, "secret" : secret})
        resp.raise_for_status()
        return resp.json()
