import os
import sys

import mock
from pvHelpers.utils.certificate_bundle import CertificateBundle


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

    CertificateBundle.get_certifi_pem = mock.Mock(return_value=certifi_pem)

    if sys.platform == 'win32':
        CertificateBundle.get_pems_win = mock.Mock(return_value=os_pem)
    else:
        CertificateBundle.get_pems_darwin = mock.Mock(return_value=os_pem)

    crt_bundle = CertificateBundle(cert_path)
    assert crt_bundle.where() == cert_path

    crt_bundle.generate_and_write_pem()
    assert os.path.exists(cert_path)

    with open(cert_path) as f:
        assert f.read() == certifi_pem + os_pem

    # TODO: assert proper file permissions
