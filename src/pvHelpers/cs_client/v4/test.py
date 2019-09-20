from pvHelpers.utils import params


class TestV4(object):
    @params(object, unicode, unicode)
    def getUserSecret(self, user_id, secret_type):
        url, raw_body, headers = self.preparePublicRequest(
            u"/test/users/secret", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={"user_id": user_id, "secret_type": secret_type})
        resp.raise_for_status()
        return resp.json()

    @params(object, unicode)
    def createRecoveryRequest(self, user_id):
        url, raw_body, headers = self.preparePublicRequest(
            u"/users/approvers/secret", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={"user_id": user_id})
        resp.raise_for_status()
        return resp.json()
