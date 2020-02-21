import types

from pvHelpers.logger import g_log
from pvHelpers.proxy_config import ProxyConfig
from pvHelpers.utils import merge_dicts, params
import requests

from .session_pool import SessionPool


HTTP_TIMEOUT = 60


class HTTPClient(object):
    def __init__(self, url, default_headers=None, proxy_config=None, cert_bundle=None, session_pool=None):
        self.url = url
        self.default_headers = default_headers or {}
        self.proxy_config = proxy_config
        self.cert_bundle = cert_bundle
        self.session_pool = session_pool or SessionPool()

    @property
    def session(self):
        return self.session_pool.get(self.url)

    def accept_version(self):
        return u"v{}".format(self.__api_version__)

    def _request_common(self, method, url, **kwargs):
        _headers = merge_dicts(self.default_headers, kwargs.get('headers', {}))
        proxies = []
        if self.proxy_config:
            proxies = self.proxy_config.get_proxies(url) or []

        # Attempt relay through proxy
        while len(proxies) > 0:
            try:
                return self.session.request(
                    method, url, headers=_headers, allow_redirects=False,
                    verify=self.cert_bundle.where() if self.cert_bundle else None,
                    proxies=proxies[0], **kwargs)
            except (requests.exceptions.SSLError, requests.exceptions.InvalidProxyURL) as e:
                g_log.info("Using proxies {}".format(proxies[0]))
                g_log.exception(e)
                # refresh the cert bundle for possible addition of new certs
                if isinstance(e, requests.exceptions.SSLError) and self.cert_bundle:
                    self.cert_bundle.generate_and_write_pem()

                proxies = proxies[1:]

                # raise if no more proxies left and explicit `direct_fallback == False`
                if kwargs.get('direct_fallback', True) is False and len(proxies) == 0:
                    raise

        return self.session.request(
            method, url, headers=_headers, allow_redirects=False,
            verify=self.cert_bundle.where() if self.cert_bundle else None,
            **kwargs)

    def get(self, url, raw_body=None, params=None, timeout=HTTP_TIMEOUT, **kwargs):
        return self._request_common("GET", url, data=raw_body, params=params, timeout=timeout, **kwargs)

    def put(self, url, raw_body=None, params=None, timeout=HTTP_TIMEOUT, **kwargs):
        return self._request_common("PUT", url, data=raw_body, params=params, timeout=timeout, **kwargs)

    def post(self, url, raw_body=None, params=None, timeout=HTTP_TIMEOUT, **kwargs):
        return self._request_common("POST", url, data=raw_body, params=params, timeout=timeout, **kwargs)

    def delete(self, url, raw_body=None, params=None, timeout=HTTP_TIMEOUT, **kwargs):
        return self._request_common("DELETE", url, data=raw_body, params=params, timeout=timeout, **kwargs)

    def patch(self, url, raw_body=None, params=None, timeout=HTTP_TIMEOUT, **kwargs):
        return self._request_common("PATCH", url, data=raw_body, params=params, timeout=timeout, **kwargs)

    def prepare_signed_request(self):
        raise NotImplementedError()

    def prepare_public_request(self):
        raise NotImplementedError()
