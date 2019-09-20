class UserV5(object):
    def getUserKeyHistory(self, user):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/users/key_history", "GET", None
        )
        resp = self.get(url, headers, raw_body, params={"user_id" : user.user_id})
        resp.raise_for_status()
        return resp.json()
