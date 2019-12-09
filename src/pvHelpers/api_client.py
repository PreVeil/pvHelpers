import types

from pvHelpers.logger import g_log
from pvHelpers.proxy_config import ProxyConfig
from pvHelpers.utils import params
import requests


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
HTTP_TIMEOUT = 60
session_cache = {}


def get_session(backend, default_headers={}):
    if backend not in session_cache:
        # Let's avoid a random exploding cache.
        if len(session_cache) > 1000:
            session_cache.clear()
        session_cache[backend] = requests.Session()
        session_cache[backend].auth = NOOPAuth
        if default_headers:
            session_cache[backend].headers.update(default_headers)

    return session_cache[backend]


class APIClient(object):
    @params(object, unicode, dict, {types.NoneType, ProxyConfig})
    def __init__(self, url, default_headers={}, proxy_config=None):
        self.url = url
        self.default_headers = default_headers
        self.proxy_config = proxy_config

    @property
    def session(self):
        return get_session(self.url, self.default_headers)

    def accept_version(self):
        return u"v{}".format(self.__api_version__)

    # try each proxies in order
    # NOTEXX: tests proxy config
    def _request_with_proxies_fall_over(self, request_handle, method, url,
                                        headers, proxies, direct_fallback=True, **kwargs):
        # no proxies
        if proxies is None:
            return request_handle(method, url, headers=headers, **kwargs)

        while len(proxies) > 0:
            proxy_url = proxies[0]
            try:
                return request_handle(
                    method,
                    url,
                    headers=headers,
                    proxies=proxy_url,
                    verify=certifi_patch.where(),
                    **kwargs)
            except (requests.exceptions.SSLError,
                    requests.exceptions.InvalidProxyURL) as e:
                # what exception/error suggests a fall over
                # to the next proxy_url?
                g_log.debug("Using proxies {}".format(proxy_url))
                g_log.exception(e)
                # refresh the cert bundle since we still gets SSLError
                if isinstance(e, requests.exceptions.SSLError):
                    certifi_patch.generate_pem()
                proxies = proxies[1:]

                if not direct_fallback and len(proxies) == 0:
                    raise e

        # try "DIRECT" now since none of the given proxies work
        if direct_fallback:
            return request_handle(
                method, url, headers=headers, proxies=None, **kwargs)

    def _request_common(self, method, url, headers, raw_body=None, params=None, timeout=HTTP_TIMEOUT, **kwargs):
        session = self.session
        headers.update(session.headers)
        return self._request_with_proxies_fall_over(
            session.request,
            method,
            url,
            headers,
            proxies=self.proxy_config.get_proxies(url) if self.proxy_config is not None else None,
            data=raw_body,
            params=params,
            timeout=timeout,
            allow_redirects=False,
            **kwargs)

    def get(self,
            url,
            headers,
            raw_body=None,
            params=None,
            timeout=HTTP_TIMEOUT):
        return self._request_common("GET", url, headers, raw_body, params,
                                    timeout)

    def put(self, url, headers, raw_body=None, params=None, timeout=HTTP_TIMEOUT, **kwargs):
        return self._request_common("PUT", url, headers, raw_body, params, timeout, **kwargs)

    def post(self,
             url,
             headers,
             raw_body=None,
             params=None,
             timeout=HTTP_TIMEOUT):
        return self._request_common("POST", url, headers, raw_body, params,
                                    timeout)

    def delete(self,
               url,
               headers,
               raw_body=None,
               params=None,
               timeout=HTTP_TIMEOUT):
        return self._request_common("DELETE", url, headers, raw_body, params,
                                    timeout)

    def patch(self,
              url,
              headers,
              raw_body=None,
              params=None,
              timeout=HTTP_TIMEOUT):
        return self._request_common("PATCH", url, headers, raw_body, params,
                                    timeout)

    def prepare_signed_request(self):
        raise NotImplementedError()

    def prepare_public_request(self):
        raise NotImplementedError()
