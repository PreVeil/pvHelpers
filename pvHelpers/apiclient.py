import abc
import requests

from . import misc

class APIClient:
    __metaclass__ = abc.ABCMeta

    def __init__(self, as_user, backend):
        self.user = as_user
        self.backend = backend

    @abc.abstractmethod
    def signRequest(self, data):
        raise NotImplementedError

    def get(self, resource, params=None, timeout=misc.HTTP_TIMEOUT):
        url, _, headers = self._prepareRequest(resource, "GET", None)
        return requests.get(url, params=params, timeout=timeout, allow_redirects=False, headers=headers)

    def put(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "PUT", params)
        return requests.put(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def post(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "POST", params)
        return requests.post(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def delete(self, resource, timeout=misc.HTTP_TIMEOUT):
        url, _, headers = self._prepareRequest(resource, "DELETE", None)
        return requests.delete(url, timeout=timeout, allow_redirects=False, headers=headers)

    def patch(self, resource, params, timeout=misc.HTTP_TIMEOUT):
        url, raw_body, headers = self._prepareRequest(resource, "PATCH", params)
        return requests.patch(url, data=raw_body, timeout=timeout, allow_redirects=False, headers=headers)

    def _prepareRequest(self, resource, method, body):
        url = self.backend + resource
        if body is None:
            raw_body = u""
        else:
            raw_body = misc.jdumps(body)
        canonical_request = u"{};{};{}".format(resource, method, raw_body)
        status, signature = self.signRequest(canonical_request)
        if status == False:
            g_log.error("userSignAPI failed: %s" % self.user.email)
            raise UnableToGetTokenError()
        headers = {
            "content-type" : "application/json",
            "x-user-id"    : str(self.user.user_id),
            "x-signature"  : signature,
        }
        status, encoded_raw_body = misc.utf8Encode(raw_body)
        if status == False:
            raise UnableToGetTokenError()
        return url, encoded_raw_body, headers
