import abc
import requests

from . import misc

BACKEND_API_VERSION = "v2"

# If no authentication method is given with the auth argument, Requests will
# attempt to get the authentication credentials for the URL's hostname from
# the user's netrc file. The netrc file overrides raw HTTP authentication
# headers set with headers=.
#
# Use NOOPAuth to avoid the slow read from the netrc file.
class __NOOPAuth(requests.auth.AuthBase):
    def __call__(self, r):
        return r
NOOPAuth = __NOOPAuth()

session_cache = {}
def getSession(backend):
    if backend not in session_cache:
        # Let's avoid a random exploding cache.
        if len(session_cache) > 1000:
            session_cache.clear()
        session_cache[backend] = requests.Session()
        session_cache[backend].auth = NOOPAuth
    return session_cache[backend]

class PublicAPIClient:
    __metaclass__ = abc.ABCMeta

    def __init__(self, backend):
        self._backend = backend
        self._session = getSession(backend)

    def get(self, resource, params=None, timeout=misc.HTTP_TIMEOUT):
        url, _, headers = self._prepareRequest(resource, "GET", None)
        return self._session.get(url, params=params, timeout=timeout, allow_redirects=False, headers=headers)

    def put(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "PUT", params)
        return self._session.put(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def post(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "POST", params)
        return self._session.post(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def delete(self, resource, params=None, timeout=misc.HTTP_TIMEOUT):
        url, _, headers = self._prepareRequest(resource, "DELETE", None)
        return self._session.delete(url, params=params, timeout=timeout, allow_redirects=False, headers=headers)

    def patch(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "PATCH", params)
        return self._session.patch(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def _prepareRequest(self, resource, method, body):
        url = self._backend + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = misc.jdumps(body)

        headers = {
            "content-type" : "application/json",
            "accept-version" : BACKEND_API_VERSION,
        }
        status, encoded_raw_body = misc.utf8Encode(raw_body)
        if status == False:
            raise requests.exceptions.RequestException("failed to utf8 encode request body")
        return url, encoded_raw_body, headers

class UserAPIClient(PublicAPIClient):
    __metaclass__ = abc.ABCMeta

    def __init__(self, user_id, backend):
        super(UserAPIClient, self).__init__(backend=backend)
        self.user_id = user_id

    @abc.abstractmethod
    def signRequest(self, data):
        raise NotImplementedError

    def _prepareRequest(self, resource, method, body):
        url = self._backend + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = misc.jdumps(body)
        canonical_request = u"{};{};{}".format(resource, method, raw_body)
        status, signature = self.signRequest(canonical_request)
        if status == False:
            raise requests.exceptions.RequestException("failed to sign request")
        status, encoded_user_id = misc.utf8Encode(self.user_id)
        if status == False:
            raise requests.exceptions.RequestException("failed to utf8 encode user_id")
        headers = {
            "content-type" : "application/json",
            "x-user-id"    : encoded_user_id,
            "x-signature"  : signature,
            "accept-version" : BACKEND_API_VERSION,
        }
        status, encoded_raw_body = misc.utf8Encode(raw_body)
        if status == False:
            raise requests.exceptions.RequestException("failed to utf8 encode request body")

        return url, encoded_raw_body, headers
