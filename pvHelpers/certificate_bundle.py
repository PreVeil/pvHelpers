import codecs
import os
import re
import ssl
import subprocess
import sys

import certifi

from .misc import g_log


class CertificateBundle(object):
    def __init__(self, path):
        self.path = path

    @staticmethod
    def get_pems_win(store_names=['CA']):
        certs = []
        import wincertstore
        for store_name in store_names:
            with wincertstore.CertSystemStore(store_name) as store:
                for cert in store.itercerts(usage=wincertstore.SERVER_AUTH):
                    try:
                        pem = cert.get_pem()
                        pem_entry = '# Label: \'{name}\'\n{pem}'.format(
                            name=cert.get_name(),
                            pem=pem.decode('ascii') if isinstance(pem, bytes) else pem
                        )
                    except UnicodeEncodeError as e:
                        g_log.exception(e)
                        pem_entry = ''

                    certs.append(pem_entry)

        return certs

    @staticmethod
    def get_pems_darwin():
        certs = []
        try:
            # /usr/bin/security is owned by root. We use that to make sure find-certificate command is not a tampered version.
            # '/usr/bin/security default-keychain' shows keychains that find-certificate. This should include login and System Keychains.
            process = subprocess.Popen(['/usr/bin/security', 'find-certificate', '-ap'], stdout=subprocess.PIPE)
            stdoutdata, _ = process.communicate()
        except Exception as e:
            g_log.exception(e)
        else:
            certs.append(stdoutdata)

        return certs

    @staticmethod
    def get_pems_legacy():
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.load_default_certs()
        for der_cert in ssl_context.get_ca_certs(binary_form=True):
            yield(ssl.DER_cert_to_PEM_cert(der_cert))

    def get_certifi_pem(self):
        certifi_pem_path = certifi.where()
        if not os.path.exists(certifi_pem_path):
            raise ValueError('Cannot find certifi cacert.pem')
        with open(certifi_pem_path) as f:
            return f.read()

    def set_permissions(self):
        if sys.platform == 'win32':
            from .win_helpers import make_world_readable

            # For each directory in the path (except the root), make sure it is traversable
            # by any local user. Otherwise the PEM file cannot be read.
            p = os.path.abspath(os.path.dirname(self.path))
            while not re.compile('^\w:\\\\$').match(p):  # noqa: W605
                make_world_readable(p, True)
                p, _ = os.path.split(p)

            make_world_readable(self.path, False)

        elif sys.platform == 'darwin' or sys.platform.startswith('linux'):
            # be careful not change anything else beyond the ancestors of cacert.pem
            pem_path_splits = self.path.split(os.sep)
            for i in range(len(pem_path_splits)-2):
                p = os.sep.join(pem_path_splits[0:len(pem_path_splits)-i])
                os.chmod(p, 0755)

    def generate_and_write_pem(self):
        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path))
        f = open(self.path,"w+")
        certs = [self.get_certifi_pem()]
        if sys.platform == 'win32':
            certs += self.get_pems_win()
        elif sys.platform == 'darwin':
            certs += self.get_pems_darwin()

        # For now we need to support some potentially incompatible network configurations
        certs += self.get_pems_legacy()

        with codecs.open(self.path, 'w', 'utf-8') as f:
            for pem in certs:
                f.write(pem)

        self.set_permissions()

    def where(self):
        return self.path
