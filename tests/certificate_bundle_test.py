import os
import sys
import stat
import mock
from pvHelpers import CertificateBundle

#https://stackoverflow.com/questions/34698927/python-get-windows-folder-acl-permissions
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
    print cert_path
    certifi_pem, os_pem = '''
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
    '''

    crt_bundle = CertificateBundle(cert_path) 
    crt_bundle.get_certifi_pem = mock.Mock(return_value=certifi_pem)

    if sys.platform == 'win32':
        crt_bundle.get_pems_win = mock.Mock(return_value=os_pem)
    else:
        crt_bundle.get_pems_darwin = mock.Mock(return_value=os_pem)

    assert crt_bundle.where() == cert_path

    crt_bundle.generate_and_write_pem()
    assert os.path.exists(cert_path)

    with open(cert_path) as f:
        assert f.read() == certifi_pem + os_pem


def test_set_permissions():
    path = os.path.join(os.environ['TMPDIR'], 'cacert.pem')
    if os.path.exists(path):
        os.remove(path)
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    f = open(path,"w+")
    expected_mode = int("755", 8)
    if sys.platform == 'win32':
        assert check_user_read_permission(path) == False
    else: 
        assert stat.S_IMODE(os.stat(path).st_mode) != expected_mode

    crt_bundle = CertificateBundle(path) 
    crt_bundle.set_permissions()

    if sys.platform == 'win32':
        assert check_user_read_permission(path) == True
    else:
        assert stat.S_IMODE(os.stat(path).st_mode) == expected_mode

    assert os.access(path, os.R_OK) == True
    assert os.access(path, os.X_OK) == True
    assert os.access(path, os.W_OK) == True
test_set_permissions()