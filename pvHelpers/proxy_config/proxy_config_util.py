import os
import subprocess
import sys

from .constants import IPProtocol, ProxyKey
from ..misc import g_log
from .proxy_config_item import ProxyConfigItem, ProxyPac, ProxyUrl

if "win32" == sys.platform:
    import io
    import tempfile
    from ..misc import randUnicode
    from ..win_helpers import runWindowsProcessAsCurrentUser


def parse_os_proxy_config(scutil_proxy_conf):
    res = scutil_proxy_conf.replace(" ", "")
    res = res.split("\n")
    proxy_dict = {}
    for r in res:
        entry = r.split(":")
        if len(entry) >= 2:
            proxy_dict[entry[0]] = ":".join(entry[1:])

    return proxy_dict


def __process_darwin_proxies(config):
    proxy_item = ProxyConfigItem()
    http_enable = config.get(ProxyKey.HttpEnable)
    if http_enable == "1":
        http_proxy = config.get(ProxyKey.HttpProxy)
        http_port = config.get(ProxyKey.HttpPort)
        if http_proxy is not None and http_port is not None:
            proxy_item.add_or_update(IPProtocol.HTTP, ProxyUrl(
                IPProtocol.HTTP, http_proxy, http_port))

    https_enable = config.get(ProxyKey.HttpsEnable)
    if https_enable == "1":
        https_proxy = config.get(ProxyKey.HttpsProxy)
        https_port = config.get(ProxyKey.HttpsPort)
        if https_proxy is not None and https_port is not None:
            proxy_item.add_or_update(IPProtocol.HTTPS, ProxyUrl(
                IPProtocol.HTTPS, https_proxy, https_port))

    pac_enable = config.get(ProxyKey.ProxyAutoConfigEnable)
    if pac_enable == "1":
        proxy_item.add_or_update(IPProtocol.PAC, ProxyPac(
            config.get(ProxyKey.ProxyAutoConfigURLString)))

    return proxy_item if proxy_item.size > 0 else None


def __process_win_proxies(config):
    proxy_item = ProxyConfigItem()
    if config.get("ProxyEnable") == "1":
        proxy_server = config.get("ProxyServer")
        if proxy_server is not None:
            # each server is format as http=ip:port;https=ip:port or ip:port if each
            # protocol uses the same ip and port
            ps = proxy_server.split(";")
            for e in ps:
                scheme = e.split("=")
                if len(scheme) == 1 and e == scheme[0]:
                    # user sets only one proxy info (ip:port) for all protocols
                    # based on the internet setting UI
                    # on window 10
                    s = e.split(":")
                    if len(s) != 2:
                        g_log.warn("encounter invalid ip:port {}".format(e))
                        continue
                    ip, port = s[0], s[1]
                    proxy_item.add_or_update(
                        IPProtocol.HTTP, ProxyUrl(IPProtocol.HTTP, ip, port))
                    proxy_item.add_or_update(
                        IPProtocol.HTTPS, ProxyUrl(IPProtocol.HTTPS, ip, port))

                elif len(scheme) == 2:
                    pc = scheme[0]
                    s = scheme[1].split(":")
                    if len(s) != 2:
                        g_log.warn(
                            "encounter invalid ip:port {}".format(scheme[1]))
                        continue
                    ip, port = s[0], s[1]
                    proxy_item.add_or_update(pc, ProxyUrl(pc, ip, port))

    pac_url = config.get(ProxyKey.AutoConfigURL)
    if pac_url is not None:
        proxy_item.add_or_update(IPProtocol.PAC, ProxyPac(pac_url))

    return proxy_item if proxy_item.size > 0 else None


def process_os_proxies(proxy_config_str, platform=None):
    config = parse_os_proxy_config(proxy_config_str)

    if platform is None:
        platform = sys.platform

    if platform == "darwin":
        return __process_darwin_proxies(config)

    elif platform == "win32":
        return __process_win_proxies(config)

    return None


def get_os_proxies():
    proxy_conf_str = None
    if "darwin" == sys.platform:
        try:
            proxy_conf_str = subprocess.check_output(
                "scutil --proxy", shell=True)
        except subprocess.CalledProcessError as e:
            g_log.exception(e)
            proxy_conf_str = None

    elif "win32" == sys.platform:
        reg_internet_setting = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        ps = "C:\Windows\System32\WindowsPowerShell\\v1.0\powershell.exe"

        # the current logic of running the process as current user
        # does not give us access to the process's stdout.
        # so need to write to a temp file first then read from it. :(
        temp_path = os.path.join(
            tempfile.gettempdir(), randUnicode(5) + ".txt")
        g_log.debug(temp_path)
        cmd = "{} Get-ItemProperty -Path '{}' >> {}".format(
            ps, reg_internet_setting, temp_path)

        status = runWindowsProcessAsCurrentUser(cmd.split(" "))
        if not status:
            g_log.warn(u"Failed to fetch os proxy settings.")
            return None

        with io.open(temp_path, "r", encoding="utf16") as f:
            proxy_conf_str = f.read()

        # best effort to clean up
        # the temp file, swallow exception if failed
        try:
            os.remove(temp_path)
        except Exception as e:
            g_log.warn(e)

    if proxy_conf_str is not None:
        return process_os_proxies(proxy_conf_str)

    return None


class __ProxyConfig(object):
    def __init__(self, os_proxy_settings=None, manual_proxy_settings=None):
        self.proxies = {}

    def add_or_update(self, type_, proxy_config_item):
        if type_ in [ProxyKey.MANUAL_PROXY_SETTINGS, ProxyKey.PROXY_BASIC_AUTH, ProxyKey.OS_PROXY_SETTINGS]:
            self.proxies[type_] = proxy_config_item

            # proxy auth has to be formatted as this syntax: <protocol>://user:password@ip:port/
            # otherwise, it won't work
            # http://docs.python-requests.org/en/master/user/advanced/#proxies
            if type_ == ProxyKey.PROXY_BASIC_AUTH:
                self.set_basic_auth_cred(proxy_config_item)

    def init(self, manual_settings=None):
        self.proxies[ProxyKey.MANUAL_PROXY_SETTINGS] = manual_settings

    def get_update(self):
        self.add_or_update(ProxyKey.OS_PROXY_SETTINGS, get_os_proxies())

    @property
    def basic_auth(self):
        return self.proxies.get(ProxyKey.PROXY_BASIC_AUTH)

    @property
    def os_proxy_setting(self):
        return self.proxies.get(ProxyKey.OS_PROXY_SETTINGS)

    @property
    def manual_proxy_setting(self):
        return self.proxies.get(ProxyKey.MANUAL_PROXY_SETTINGS)

    def set_basic_auth_cred(self, basic_auth):
        if self.manual_proxy_setting is not None:
            self.manual_proxy_setting.set_basic_auth_cred(basic_auth)
        elif self.os_proxy_setting is not None:
            self.os_proxy_setting.set_basic_auth_cred(basic_auth)

    def get_proxies(self, url=None):
        if self.manual_proxy_setting is not None:
            return self.manual_proxy_setting.get_proxies(url)
        if self.os_proxy_setting is not None:
            return self.os_proxy_setting.get_proxies(url)
        return None

    def toDict(self):
        if self.manual_proxy_setting is not None:
            return {"setting_type": "manual", "setting_values": self.manual_proxy_setting.toDict()}
        if self.os_proxy_setting is not None:
            return {"setting_type": "os", "setting_values": self.os_proxy_setting.toDict()}
        return {"setting_type": None, "setting_values": {}}


ProxyConfig = __ProxyConfig()