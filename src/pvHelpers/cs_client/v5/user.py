class UserV5(object):
    def get_user_key_history(self, user):
        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/users/key_history", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={"user_id": user.user_id})
        resp.raise_for_status()
        return resp.json()
