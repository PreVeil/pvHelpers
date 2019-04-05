import pacparser
import requests

from ..misc import g_log

RETRYABLE_EXCEPTION = (requests.exceptions.ConnectionError,
                       requests.exceptions.Timeout)


class Pac(object):
    def __init__(self, pac_url, proxy_auth=None):
        self.pac_url = pac_url
        self.proxy_auth = proxy_auth
        self.fetched = False
        self.__parse_pac()

    def __parse_pac(self):
        retry, downloaded_pac = download_url(self.pac_url, download_pac)

        # connection error, we are gonna retry
        # when get_proxies() gets called.
        if retry:
            self.fetched = False
            return

        # either download succeeded, or it is not a valid url, then falls back to
        # a file path.
        try:
            pacparser.init()
            if downloaded_pac is not None:
                g_log.debug("pac url is a url: {}".format(self.pac_url))
                pacparser.parse_pac_string(downloaded_pac)
            else:
                g_log.debug("pac url is a local file: {}".format(self.pac_url))
                pacparser.parse_pac_file(self.pac_url)
        except IOError:
            # neither a valid url or valid file path
            self.clean_up()
            raise
        else:
            self.fetched = True

    def __get_proxies(self, url, host=None):
        """
        :return: a string of proxies from FindProxyForURL() in pac file js
        or 'None' if we can't process the url.
        """

        if not self.fetched:
            self.__parse_pac()

        try:
            proxy_str = pacparser.find_proxy(url, host)
        except pacparser.URLError as e:
            g_log.error(e)
            return None
        else:
            return parse_pac_value(proxy_str, self.proxy_auth)

    def get_proxies(self, url, host=None):
        """
        :return: a list of proxy dict that can be passed to
        requests' proxies parameter. Each proxy dict is meant to be used in a
        fallover fashion. 'None' means the url requires no proxy.
        """

        proxy_list = self.__get_proxies(url, host)
        if not proxy_list:
            return None

        proxies_for_requests = []
        for proxy in proxy_list:
            if proxy != "DIRECT":
                proxies_for_requests.append({
                    "http": proxy,
                    "https": proxy,
                })

        return proxies_for_requests if len(proxies_for_requests) > 0 else None

    def clean_up(self):
        self.fetched = False
        pacparser.cleanup()


def download_url(url, download_handler):
    """
    :return: retryable, content of the pac url
    """
    try:
        return False, download_handler([url])
    except requests.RequestException as e:
        if isinstance(e, RETRYABLE_EXCEPTION):
            return True, None
    return False, None


"""
The following helpers are lifted from pypac.
"""


def download_pac(candidate_urls, timeout=1, allowed_content_types=None):
    """
    Try to download a PAC file from one of the given candidate URLs.
    :param list[str] candidate_urls: URLs that are expected to return a PAC file.
        Requests are made in order, one by one.
    :param timeout: Time to wait for host resolution and response for each URL.
        When a timeout or DNS failure occurs, the next candidate URL is tried.
    :param allowed_content_types: If the response has a ``Content-Type`` header,
        then consider the response to be a PAC file only if the header is one of these values.
        If not specified, the allowed types are
        ``application/x-ns-proxy-autoconfig`` and ``application/x-javascript-config``.
    :return: Contents of the PAC file, or `None` if no URL was successful.
    :rtype: str|None
    """
    if not allowed_content_types:
        allowed_content_types = {
            "application/x-ns-proxy-autoconfig",
            "application/x-javascript-config"
        }

    sess = requests.Session()
    # Don't inherit proxy config from environment variables.
    sess.trust_env = False
    for pac_url in candidate_urls:
        try:
            resp = sess.get(pac_url, timeout=timeout)
            content_type = resp.headers.get("content-type", "").lower()
            if content_type and True not in [
                    allowed_type in content_type
                    for allowed_type in allowed_content_types
            ]:
                continue
            if resp.ok:
                return resp.text
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:
            g_log.exception(e)
            continue


def parse_pac_value(value, proxy_auth=None, socks_scheme=None):
    """
    Parse the return value of ``FindProxyForURL()`` into a list.
    List elements will either be the string "DIRECT" or a proxy URL.

    For example, the result of parsing ``PROXY example.local:8080; DIRECT``
    is a list containing strings ``http://example.local:8080`` and ``DIRECT``.
    Also includes the proxy auth creds if provided.

    :param str value: Any value returned by ``FindProxyForURL()``.
    :param str socks_scheme: Scheme to assume for SOCKS proxies. ``socks5`` by default.
    :returns: Parsed output, with invalid elements ignored. Warnings are logged for invalid elements.
    :rtype: list[str]
    """
    config = []
    for element in value.split(";"):
        element = element.strip()
        if not element:
            continue
        try:
            config.append(proxy_url(element, proxy_auth, socks_scheme))
        except ValueError as e:
            g_log.warn(e)
    return config


def proxy_url(value, proxy_auth=None, socks_scheme=None):
    """
    Parse a single proxy config value from FindProxyForURL() into a more usable element.

    :param str value: Value to parse, e.g.: ``DIRECT``, ``PROXY example.local:8080``, or ``SOCKS example.local:8080``.
    :param str socks_scheme: Scheme to assume for SOCKS proxies. ``socks5`` by default.
    :returns: Parsed value, e.g.: ``DIRECT``, ``http://example.local:8080``, or ``socks5://example.local:8080``.
    :rtype: str
    :raises ValueError: If input value is invalid.
    """
    if value.upper() == "DIRECT":
        return "DIRECT"
    parts = value.split()

    if len(parts) == 2:
        keyword, proxy = parts[0].upper(), parts[1]
        if keyword == "PROXY":
            if proxy_auth:
                return "http://{}:{}@{}".format(proxy_auth.username,
                                                proxy_auth.password, proxy)
            return "http://" + proxy
        elif keyword == "SOCKS":
            if not socks_scheme:
                socks_scheme = "socks5"
            if proxy_auth:
                return "{}://{}:{}@{}".format(socks_scheme,
                                              proxy_auth.username,
                                              proxy_auth.password, proxy)
            return "{}://{}".format(socks_scheme, proxy)

        # TODO: also support keyword 'HTTP' and 'HTTPS'
        # as describe here: https://developer.mozilla.org/en-US/docs/Web/HTTP/Proxy_servers_and_tunneling/Proxy_Auto-Configuration_(PAC)_file

    raise ValueError("Unrecognized proxy config value '{}'".format(value))
