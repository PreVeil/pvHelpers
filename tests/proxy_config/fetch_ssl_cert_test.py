import pvHelpers as H
import sys
import os
import time
import subprocess
import certifi
import pem
import pytest
from pvHelpers import CertificateBundle

@pytest.mark.skipif(sys.platform != "win32", reason="win specific test")
def test_fetch_cert_from_trust_root_cert_ca():
    # get the self-signed cert
    proxy_cert = pem.parse_file(os.path.join(
        H.getdir(__file__), "insecure.pem"))[-1]

    original_where = certifi.where()
    assert original_where == os.path.join(
        os.path.split(certifi.__file__)[0], "cacert.pem")
    original_certs = pem.parse_file(original_where)
    assert proxy_cert not in original_certs

    def _subprocess_run(cmd):
        return subprocess.check_output(
            cmd, cwd=H.getdir(__file__), shell=True, stderr=subprocess.STDOUT)

    def import_cert_root_store(capath):
        # import the self signed cert
        # to window's Trusted Root Certification Authorities
        ps = "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
        cmd = "{} import-certificate -Filepath {} -CertStoreLocation cert:/LocalMachine/CA".format(
            ps, capath)

        return _subprocess_run(cmd)

    def remove_cert_root_store():
        ps = "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
        cmd = "{} {}".format(ps, os.path.join(
            H.getdir(__file__), "remove_cert.ps1"))

        return _subprocess_run(cmd)

    def patch_certifi(path):
        patched_certs = pem.parse_file(path)
        assert len(patched_certs) > len(original_certs)

        # look for the self-signed cert
        # compare them line by line
        found = False
        a = proxy_cert.as_text().split("\n")
        for cert in patched_certs:
            b = cert.as_text().split("\n")
            if len(a) == len(b) and a[1].strip() == b[1].strip():
                for i in range(2, len(a)):
                    assert a[i].strip() == b[i].strip()
                found = True
        return found

    import_cert_root_store(os.path.join(
        H.getdir(__file__), "insecure.crt"))

    # 60 seconds timeout for cert to be found
    path = os.path.join(os.environ['TMPDIR'], 'cacert2.pem')
    crt = CertificateBundle(path)
    crt.generate_and_write_pem()
    t = time.time()
    while time.time() - t < 60:
        if patch_certifi(crt.where()):
            remove_cert_root_store()
            return
        time.sleep(1)
        crt.generate_and_write_pem()
    pytest.fail("cert not found!")
