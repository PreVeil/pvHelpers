from pvHelpers.utils import params


class TestV4(object):
    @params(object, unicode, unicode)
    def get_user_secret(self, user_id, secret_type):
        url, raw_body, headers = self.prepare_public_request(
            u"/test/users/secret", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={"user_id": user_id, "secret_type": secret_type})
        resp.raise_for_status()
        return resp.json()

    @params(object, unicode)
    def create_recovery_request(self, user_id):
        url, raw_body, headers = self.prepare_public_request(
            u"/users/approvers/secret", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={"user_id": user_id})
        resp.raise_for_status()
        return resp.json()