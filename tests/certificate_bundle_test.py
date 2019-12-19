from pvHelpers import CertificateBundle
import tempfile
import os 
import mock
import sys

def test_generate_pem():
    tempd_path = tempfile.mkdtemp()
    cert_path = os.path.join(os.path.abspath(tempd_path), "cacert.pem")
    open(cert_path, "w")

    crt_bundle = CertificateBundle(cert_path)
    certifi_pem = """
        -----BEGIN CERTIFICATE-----
        En02p1ttZk/roboOu4h78EjBjGc6EqCafwPyOXP84NxhryPFB3k4WOcyh8yjQjBA
        MA4GA1UdDwEB/wQEAwIBhjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBQ5qzN/
        KPlne+nW++PwX9t4OYy1AjAKBggqhkjOPQQDAgNIADBFAiEA/OFu3wo0rc63YPd7
        Ni3hG6LL4KW3KVJkSly+wXTlXZYCIE15amagmRDjP1bglzyAxQyhaWtj7+/OjwSx
        -----END CERTIFICATE-----
        """
    os_pem = """
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
        """

    CertificateBundle.get_certifi_pem = mock.Mock(return_value=certifi_pem)

    if sys.platform == "win32": 
        CertificateBundle.get_pems_win = mock.Mock(return_value=os_pem)
    else: 
        CertificateBundle.get_pems_osx = mock.Mock(return_value=os_pem)

    crt_bundle.generate_pem()

    assert os.path.exists(cert_path) == True
    
    read_file = ""
    with open(cert_path) as f: 
        read_file = f.read()
    assert read_file == certifi_pem + os_pem
    
    assert crt_bundle.where() == cert_path        
