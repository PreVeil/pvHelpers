import os
import pytest
from requests.auth import HTTPProxyAuth
from pvHelpers import ProxyConfig, process_os_proxies, ProxyPac, Pac, getdir

# mimic proxy config dictionary from win32 and osx
win_no_proxy = """DisableCachingOfSSLPages : 0
        IE5_UA_Backup_Flag       : 5.0
        PrivacyAdvanced          : 1
        SecureProtocols          : 2688
        CertificateRevocation    : 1
        User Agent               : Mozilla/4.0 (compatible; MSIE 8.0; Win32)
        ZonesSecurityUpgrade     : {255, 153, 74, 53...}
        EnableNegotiate          : 1
        MigrateProxy             : 1
        WarnonZoneCrossing       : 0
        LockDatabase             : 131945979334162163
        ProxyOverride            : <local>
        PSPath                   : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
        PSParentPath             : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion
        PSChildName              : Internet Settings
        PSDrive                  : HKCU
        PSProvider               : Microsoft.PowerShell.Core\Registry
    """

win_proxy_str_inenable = """DisableCachingOfSSLPages : 0
        IE5_UA_Backup_Flag       : 5.0
        PrivacyAdvanced          : 1
        SecureProtocols          : 2688
        CertificateRevocation    : 1
        User Agent               : Mozilla/4.0 (compatible; MSIE 8.0; Win32)
        ZonesSecurityUpgrade     : {255, 153, 74, 53...}
        EnableNegotiate          : 1
        MigrateProxy             : 1
        ProxyEnable              : 0
        WarnonZoneCrossing       : 0
        LockDatabase             : 131945979334162163
        ProxyServer              : http=localhost:3333
        ProxyOverride            : <local>
        PSPath                   : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
        PSParentPath             : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion
        PSChildName              : Internet Settings
        PSDrive                  : HKCU
        PSProvider               : Microsoft.PowerShell.Core\Registry
    """

win_proxy_str_pac = """DisableCachingOfSSLPages : 0
        IE5_UA_Backup_Flag       : 5.0
        PrivacyAdvanced          : 1
        SecureProtocols          : 2688
        CertificateRevocation    : 1
        User Agent               : Mozilla/4.0 (compatible; MSIE 8.0; Win32)
        ZonesSecurityUpgrade     : {255, 153, 74, 53...}
        EnableNegotiate          : 1
        MigrateProxy             : 1
        ProxyEnable              : 0
        WarnonZoneCrossing       : 0
        LockDatabase             : 131945979334162163
        ProxyServer              : localhost:3128
        ProxyOverride            : <local>
        AutoConfigURL            : C:\Users\preveil\Desktop\pv-pac.pac
        PSPath                   : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
        PSParentPath             : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion
        PSChildName              : Internet Settings
        PSDrive                  : HKCU
        PSProvider               : Microsoft.PowerShell.Core\Registry
    """

win_proxy_str = """DisableCachingOfSSLPages : 0
        IE5_UA_Backup_Flag       : 5.0
        PrivacyAdvanced          : 1
        SecureProtocols          : 2688
        CertificateRevocation    : 1
        User Agent               : Mozilla/4.0 (compatible; MSIE 8.0; Win32)
        ZonesSecurityUpgrade     : {255, 153, 74, 53...}
        EnableNegotiate          : 1
        MigrateProxy             : 1
        ProxyEnable              : 1
        WarnonZoneCrossing       : 0
        LockDatabase             : 131945979334162163
        ProxyServer              : http=localhost:3333;https=ppp;ftp=hhh:3128
        ProxyOverride            : <local>
        PSPath                   : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
        PSParentPath             : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion
        PSChildName              : Internet Settings
        PSDrive                  : HKCU
        PSProvider               : Microsoft.PowerShell.Core\Registry
    """

win_proxy_str_one_ip_port_for_all = """DisableCachingOfSSLPages : 0
        IE5_UA_Backup_Flag       : 5.0
        PrivacyAdvanced          : 1
        SecureProtocols          : 2688
        CertificateRevocation    : 1
        User Agent               : Mozilla/4.0 (compatible; MSIE 8.0; Win32)
        ZonesSecurityUpgrade     : {255, 153, 74, 53...}
        EnableNegotiate          : 1
        MigrateProxy             : 1
        ProxyEnable              : 1
        WarnonZoneCrossing       : 0
        LockDatabase             : 131945979334162163
        ProxyServer              : localhost:2121
        ProxyOverride            : <local>
        PSPath                   : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
        PSParentPath             : Microsoft.PowerShell.Core\Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion
        PSChildName              : Internet Settings
        PSDrive                  : HKCU
        PSProvider               : Microsoft.PowerShell.Core\Registry
    """

scutil_no_proxy = """<dictionary > {
            HTTPEnable: 0
            HTTPSEnable: 0
    }"""

scutil_with_proxy = """<dictionary > {
            HTTPEnable: 1
            HTTPPort: 3128
            HTTPProxy: localhost
            HTTPSEnable: 1
            HTTPSPort: 2222
            HTTPSProxy: localhost
            ProxyAutoConfigEnable: 1
            ProxyAutoConfigURLString: some_pac.pac
    }"""

scutil_with_proxy_info_inenable = """<dictionary > {
            HTTPEnable: 0
            HTTPPort: 3128
            HTTPProxy: 167.0.0.1
            HTTPSEnable: 1
            HTTPSPort: 2222
            HTTPSProxy: localhost
            ProxyAutoConfigEnable: 0
            ProxyAutoConfigURLString: some_pac.pac
    }"""

Proxy_Dicts = [win_no_proxy,
               win_proxy_str, win_proxy_str_inenable, win_proxy_str_pac,
               win_proxy_str_one_ip_port_for_all,
               scutil_no_proxy, scutil_with_proxy, scutil_with_proxy_info_inenable]


def test_OS_proxy_processer():
    # win32
    assert process_os_proxies(win_no_proxy, "win32") is None
    assert process_os_proxies(win_proxy_str_inenable, "win32") is None
    assert process_os_proxies(win_proxy_str_one_ip_port_for_all, "win32").toDict() == \
        {"http": {"username": None, "ip": "localhost", "password": None, "protocol": "http", "port": "2121"},
         "https": {"username": None, "ip": "localhost", "password": None, "protocol": "https", "port": "2121"}}

    assert process_os_proxies(win_proxy_str, "win32").toDict() == \
        {"http": {"username": None, "ip": "localhost",
                  "password": None, "protocol": "http", "port": "3333"}}
    assert process_os_proxies(win_proxy_str_pac, "win32").toDict() == \
        {"pac": {"pac_url": "C:\\Users\\preveil\\Desktop\\pv-pac.pac"}}

    # darwin
    assert process_os_proxies(scutil_no_proxy, "darwin") is None
    assert process_os_proxies(scutil_with_proxy_info_inenable, "darwin").toDict() == \
        {"https": {"username": None, "ip": "localhost",
                   "password": None, "protocol": "https", "port": "2222"}}
    assert process_os_proxies(scutil_with_proxy, "darwin").toDict() == \
        {"pac": {"pac_url": "some_pac.pac"},
         "http": {"username": None, "ip": "localhost", "password": None, "protocol": "http", "port": "3128"},
         "https": {"username": None, "ip": "localhost", "password": None, "protocol": "https", "port": "2222"}}


def test_bad_pacfile():
    # make sure we don't crash if provided bad pac file
    with pytest.raises(IOError):
        Pac("http://not_exist_pac.pac")

    with pytest.raises(IOError):
        Pac("C:\Users\\some_where.pac")

    bad_pac_file = os.path.join(getdir(__file__), "bad_pac_file.pac")
    a = Pac(bad_pac_file)
    with pytest.raises(Exception):
        a.get_proxies("https://preveil.com")

    test_pac_file = os.path.join(getdir(__file__), "test_pac_file.pac")
    pac = Pac(test_pac_file)

    assert pac.get_proxies("https://collections.preveil.com") == \
        [
            {"https": "http://199.168.151.10:10975",
             "http": "http://199.168.151.10:10975"},
            {"https": "http://104.129.194.41:10975",
             "http": "http://104.129.194.41:10975"}
    ]

    assert pac.get_proxies("adsfads") is None

    proxy_pac = ProxyPac(test_pac_file)
    proxy_pac.set_basic_auth_cred(HTTPProxyAuth("user", "pass"))
    assert proxy_pac.get_proxies("https://collections.preveil.com") == \
        [
            {"https": "http://user:pass@199.168.151.10:10975",
             "http": "http://user:pass@199.168.151.10:10975"},
            {"https": "http://user:pass@104.129.194.41:10975",
             "http": "http://user:pass@104.129.194.41:10975"}
    ]


def test_proxy_config_operations():
    pass
