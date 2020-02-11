import os
import stat
import sys

import mock
from pvHelpers.utils import CertificateBundle


# https://stackoverflow.com/questions/34698927/python-get-windows-folder-acl-permissions
def check_user_read_permission(path):
    import ntsecuritycon
    import win32security
    users, _, _ = win32security.LookupAccountName('', 'USERS')
    sd = win32security.GetFileSecurity(path, win32security.DACL_SECURITY_INFORMATION)
    dacl = sd.GetSecurityDescriptorDacl()
    for entry in dacl.GetExplicitEntriesFromAcl():
        if entry["Trustee"]["Identifier"] == users:
            if entry["AccessPermissions"] == ntsecuritycon.FILE_GENERIC_READ:
                return True
    return False


def test_generate_pem():
    cert_path = os.path.join(os.environ['TMPDIR'], 'cacert.pem')

    certifi_pem, os_pem, legacy_pem = '''
        -----BEGIN CERTIFICATE-----
        En02p1ttZk/roboOu4h78EjBjGc6EqCafwPyOXP84NxhryPFB3k4WOcyh8yjQjBA
        MA4GA1UdDwEB/wQEAwIBhjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBQ5qzN/
        KPlne+nW++PwX9t4OYy1AjAKBggqhkjOPQQDAgNIADBFAiEA/OFu3wo0rc63YPd7
        Ni3hG6LL4KW3KVJkSly+wXTlXZYCIE15amagmRDjP1bglzyAxQyhaWtj7+/OjwSx
        -----END CERTIFICATE-----
    ''', '''
        -----BEGIN CERTIFICATE-----
        OS102p1ttZk/roboOu4h78EjBjGc6EqCafwPyOXP84NxhryPFB3k4WOcyh8yjQjBA
        MA4GA1UdDwEB/wQEAwIBhjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBQ5qzN/
        KPlne+nW++PwX9t4OYy1AjAKBggqhkjOPQQDAgNIADBFAiEA/OFu3wo0rc63YPd7
        Ni3hG6LL4KW3KVJkSly+wXTlXZIE15amagmRDjP1bglzyAxQyhaWtj7+/OjwSxYC
        -----END CERTIFICATE-----
        -----BEGIN CERTIFICATE-----
        OS22p1ttZk/roboOu4h78EjBjGc6EqCafwPyOXP84NxhryPFB3k4WOcyh8yjQjBA
        MA4GA1UdDwEB/wQEAwIBhjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBQ5qzN/
        KPlne+nW++PwX9t4OYy1AjAKBggqhkjOPQQDAgNIADBFAiEA/OFu3wo0rc63YPd7
        Ni3hG6LL4KW3KVJkSly1bglzyAxQyhaWtj7+/OjwSx+wXTlXZYCIE15amagmRDjP
        -----END CERTIFICATE-----
        -----BEGIN CERTIFICATE-----
        OS33p1ttZk/roboOu4h78EjBjGc6EqCafwPyOXP84NxhryPFB3k4WOcyh8yjQjBA
        MA4GA1UdDwEB/wQEAwIBhjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBQ5qzN/
        KPlne+nW++PwX9t4OYy1YCIE15amagmRDjP1bglzyAxQyhaWtj7+/OjwSxDBFAiE
        Ni3hG6LL4KW3KVJkSly+wXTlXZYCIE15amagmRDjP1bglzyDBFAiEA/OFu3wo0rc
        -----END CERTIFICATE-----
    ''', '''
        -----BEGIN CERTIFICATE-----
        MIICDDCCAZGgAwIBAgIQbkepx2ypcyRAiQ8DVd2NHTAKBggqhkjOPQQDAzBHMQsw
        CQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2VzIExMQzEU
        MBIGA1UEAxMLR1RTIFJvb3QgUjMwHhcNMTYwNjIyMDAwMDAwWhcNMzYwNjIyMDAw
        MDAwWjBHMQswCQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZp
        Y2VzIExMQzEUMBIGA1UEAxMLR1RTIFJvb3QgUjMwdjAQBgcqhkjOPQIBBgUrgQQA
        IgNiAAQfTzOHMymKoYTey8chWEGJ6ladK0uFxh1MJ7x/JlFyb+Kf1qPKzEUURout
        736GjOyxfi//qXGdGIRFBEFVbivqJn+7kAHjSxm65FSWRQmx1WyRRK2EE46ajA2A
        DDL24CejQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNVHRMBAf8EBTADAQH/MB0GA1Ud
        DgQWBBTB8Sa6oC2uhYHP0/EqEr24Cmf9vDAKBggqhkjOPQQDAwNpADBmAjEAgFuk
        fCPAlaUs3L6JbyO5o91lAFJekazInXJ0glMLfalAvWhgxeG4VDvBNhcl2MG9AjEA
        njWSdIUlUfUk7GRSJFClH9voy8l27OyCbvWFGFPouOOaKaqW04MjyaR7YbPMAuhd
        -----END CERTIFICATE-----
    '''

    crt_bundle = CertificateBundle(cert_path)
    crt_bundle.get_certifi_pem = mock.Mock(return_value=certifi_pem)
    crt_bundle.get_pems_legacy = mock.Mock(return_value=legacy_pem)

    if sys.platform == 'win32':
        crt_bundle.get_pems_win = mock.Mock(return_value=os_pem)
    else:
        crt_bundle.get_pems_darwin = mock.Mock(return_value=os_pem)

    assert crt_bundle.where() == cert_path

    crt_bundle.generate_and_write_pem()
    assert os.path.exists(cert_path)

    with open(cert_path) as f:
        assert f.read() == certifi_pem + os_pem + legacy_pem


def test_set_permissions():
    path = os.path.join(os.environ['TMPDIR'], 'test.pem')
    _ = open(path, "w+")
    expected_mode = int("755", 8)
    if sys.platform == 'win32':
        assert check_user_read_permission(path) is False
    else:
        assert stat.S_IMODE(os.stat(path).st_mode) != expected_mode

    crt_bundle = CertificateBundle(path)
    crt_bundle.set_permissions()

    if sys.platform == 'win32':
        assert check_user_read_permission(path) is True
    else:
        assert stat.S_IMODE(os.stat(path).st_mode) == expected_mode
