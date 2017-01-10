import abc
import requests

from . import misc

BACKEND_API_VERSION = "v2"

session_cache = {}
def getSession(backend):
    if backend not in session_cache:
        # Let's avoid a random exploding cache.
        if len(session_cache) > 1000:
            session_cache.clear()
        session_cache[backend] = requests.Session()
    return session_cache[backend]

class APIClient:
    __metaclass__ = abc.ABCMeta

    def __init__(self, as_user, backend):
        self.user = as_user
        self.backend = backend
        self.__session = getSession(backend)

    @abc.abstractmethod
    def signRequest(self, data):
        raise NotImplementedError

    def get(self, resource, params=None, timeout=misc.HTTP_TIMEOUT):
        url, _, headers = self._prepareRequest(resource, "GET", None)
        return self.__session.get(url, params=params, timeout=timeout, allow_redirects=False, headers=headers)

    def put(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "PUT", params)
        return self.__session.put(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def post(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "POST", params)
        return self.__session.post(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def delete(self, resource, params=None, timeout=misc.HTTP_TIMEOUT):
        url, _, headers = self._prepareRequest(resource, "DELETE", None)
        return self.__session.delete(url, params=params, timeout=timeout, allow_redirects=False, headers=headers)

    def patch(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "PATCH", params)
        return self.__session.patch(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def _prepareRequest(self, resource, method, body):
        url = self.backend + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = misc.jdumps(body)
        canonical_request = u"{};{};{}".format(resource, method, raw_body)
        status, signature = self.signRequest(canonical_request)
        if status == False:
            raise requests.exceptions.RequestException("failed to sign request")
        status, encoded_user_id = misc.utf8Encode(self.user.user_id)
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
