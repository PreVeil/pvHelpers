import os
import subprocess
import sys

from ..misc import g_log
from .constants import IPProtocol, ProxyKey
from .proxy_config_item import ProxyConfigItem, ProxyPac, ProxyUrl

if "win32" == sys.platform:
    import io
    import tempfile
    from ..misc import randUnicode
    from ..win_helpers import runWindowsProcessAsCurrentUser


def parseOSProxyConfig(scutil_proxy_conf):
    res = scutil_proxy_conf.replace(" ", "")
    res = res.split("\n")
    proxy_dict = {}
    for r in res:
        entry = r.split(":")
        if len(entry) >= 2:
            proxy_dict[entry[0]] = ":".join(entry[1:])

    return proxy_dict


def __processDarwinProxies(config):
    proxy_item = ProxyConfigItem()
    http_enable = config.get(ProxyKey.HTTPEnable)
    if http_enable == "1":
        HTTPProxy = config.get(ProxyKey.HTTPProxy)
        HTTPPort = config.get(ProxyKey.HTTPPort)
        if HTTPProxy is not None and HTTPPort is not None:
            proxy_item.addOrUpdate(IPProtocol.HTTP, ProxyUrl(
                IPProtocol.HTTP, HTTPProxy, HTTPPort))

    https_enable = config.get(ProxyKey.HTTPSEnable)
    if https_enable == "1":
        HTTPSProxy = config.get(ProxyKey.HTTPSProxy)
        HTTPSPort = config.get(ProxyKey.HTTPSPort)
        if HTTPSProxy is not None and HTTPSPort is not None:
            proxy_item.addOrUpdate(IPProtocol.HTTPS, ProxyUrl(
                IPProtocol.HTTPS, HTTPSProxy, HTTPSPort))

    pac_enable = config.get(ProxyKey.ProxyAutoConfigEnable)
    if pac_enable == "1":
        proxy_item.addOrUpdate(IPProtocol.PAC, ProxyPac(
            config.get(ProxyKey.ProxyAutoConfigURLString)))

    return proxy_item if proxy_item.size > 0 else None


def __processWinProxies(config):
    proxy_item = ProxyConfigItem()
    enable = config.get("ProxyEnable")
    if enable == "1":
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
                    proxy_item.addOrUpdate(
                        IPProtocol.HTTP, ProxyUrl(IPProtocol.HTTP, ip, port))
                    proxy_item.addOrUpdate(
                        IPProtocol.HTTPS, ProxyUrl(IPProtocol.HTTPS, ip, port))

                elif len(scheme) == 2:
                    pc = scheme[0]
                    s = scheme[1].split(":")
                    if len(s) != 2:
                        g_log.warn(
                            "encounter invalid ip:port {}".format(scheme[1]))
                        continue
                    ip, port = s[0], s[1]
                    proxy_item.addOrUpdate(pc, ProxyUrl(pc, ip, port))

    pac_url = config.get(ProxyKey.AutoConfigURL)
    if pac_url is not None:
        proxy_item.addOrUpdate(IPProtocol.PAC, ProxyPac(pac_url))

    return proxy_item if proxy_item.size > 0 else None


def processOSProxies(proxy_config_str, platform=None):
    config = parseOSProxyConfig(proxy_config_str)

    if platform is None:
        platform = sys.platform

    if platform == "darwin":
        return __processDarwinProxies(config)

    elif platform == "win32":
        return __processWinProxies(config)

    return None


def getOSProxies():
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
        return processOSProxies(proxy_conf_str)

    return None


class __ProxyConfig(object):
    def __init__(self, os_proxy_settings=None, manual_proxy_settings=None):
        self.proxies = {}

    def addOrUpdate(self, type_, proxy_config_item):
        if type_ in [ProxyKey.MANUAL_PROXY_SETTINGS, ProxyKey.PROXY_BASIC_AUTH, ProxyKey.OS_PROXY_SETTINGS]:
            self.proxies[type_] = proxy_config_item

            # proxy auth has to be formatted as this syntax: <protocol>://user:password@ip:port/
            # otherwise, it won't work
            # http://docs.python-requests.org/en/master/user/advanced/#proxies
            if type_ == ProxyKey.PROXY_BASIC_AUTH:
                self.setBasicAuthCred(proxy_config_item)

    def init(self, manual_settings=None):
        self.proxies[ProxyKey.MANUAL_PROXY_SETTINGS] = manual_settings

    def getUpdate(self):
        self.addOrUpdate(ProxyKey.OS_PROXY_SETTINGS, getOSProxies())

    @property
    def basic_auth(self):
        return self.proxies.get(ProxyKey.PROXY_BASIC_AUTH)

    @property
    def os_proxy_setting(self):
        return self.proxies.get(ProxyKey.OS_PROXY_SETTINGS)

    @property
    def manual_proxy_setting(self):
        return self.proxies.get(ProxyKey.MANUAL_PROXY_SETTINGS)

    def setBasicAuthCred(self, basic_auth):
        if self.manual_proxy_setting is not None:
            self.manual_proxy_setting.setBasicAuthCred(basic_auth)
        elif self.os_proxy_setting is not None:
            self.os_proxy_setting.setBasicAuthCred(basic_auth)

    def getProxies(self, url=None):
        if self.manual_proxy_setting is not None:
            return self.manual_proxy_setting.getProxies(url)
        if self.os_proxy_setting is not None:
            return self.os_proxy_setting.getProxies(url)
        return None

    def toBrowser(self):
        if self.manual_proxy_setting is not None:
            return {"setting_type": "manual", "setting_values": self.manual_proxy_setting.toBrowser()}
        if self.os_proxy_setting is not None:
            return {"setting_type": "os", "setting_values": self.os_proxy_setting.toBrowser()}
        return {"setting_type": None, "setting_values": {}}


ProxyConfig = __ProxyConfig()
