import requests


# If no authentication method is given with the auth argument, Requests will
# attempt to get the authentication credentials for the URL's hostname from
# the user's netrc file. The netrc file overrides raw HTTP authentication
# headers set with headers=.
# Use NOOPAuth to avoid the slow read from the netrc file.
class _NOOPAuth(requests.auth.AuthBase):
    def __call__(self, r):
        return r


session_cache = {}


class SessionPool(object):
    def get(self, backend):
        if backend not in session_cache:
            # Let's avoid a random exploding cache.
            if len(session_cache) > 1000:
                session_cache.clear()
            session_cache[backend] = requests.Session()
            session_cache[backend].auth = _NOOPAuth()
        return session_cache[backend]
