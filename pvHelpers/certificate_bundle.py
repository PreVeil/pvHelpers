
import os
import sys
import re
import subprocess

class CertificateBundle(object):
    def get_pems_win(store_names=None):
        certs = []
        try:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.load_default_certs()
            for der_cert in ssl_context.get_ca_certs(binary_form=True):
                certs.append(ssl.DER_cert_to_PEM_cert(der_cert))
        except AttributeError:
                # retrieve window certs
                import wincertstore
                store_names = store_names or ('CA', 'ROOT')
                for store_name in store_names:
                    with wincertstore.CertSystemStore(store_name) as store:
                        for cert in store.itercerts(usage=wincertstore.SERVER_AUTH):
                            try:
                                pem = cert.get_pem()
                                pem_entry = '# Label: "{name}"\n{pem}'.format(
                                    name=cert.get_name(),
                                    pem=pem.decode('ascii') if isinstance(pem, bytes) else pem
                                )
                            except UnicodeEncodeError:
                                pem_entry = ''

                            certs.append(pem_entry)
        return certs


    def get_pems_osx(self):
        certs = []
        try:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.load_default_certs()
            for der_cert in ssl_context.get_ca_certs(binary_form=True):
                certs.append(ssl.DER_cert_to_PEM_cert(der_cert))
            process = subprocess.Popen(["/usr/bin/security", "find-certificate", "-ap"], stdout=subprocess.PIPE)
            stdoutdata, stderrdata = process.communicate()
            certs.append(stdoutdata)
        except:
            pass
        return certs
            
    def add_certifi_pem(self, path):
        import certifi
        certifi_pem = os.path.join(os.path.split(certifi.__file__)[0], 'cacert.pem')
        if not os.path.exists(certifi_pem):
            raise ValueError('Cannot find certifi cacert.pem')
        import shutil
        shutil.copy(certifi_pem, path)


    def create_pem_path(self, path):
        if sys.platform == 'win32':
            import ctypes
            from ctypes import wintypes

            # Create ctypes wrapper for Win32 functions we need, with correct argument/return types
            _CreateMutex = ctypes.windll.kernel32.CreateMutexA
            _CreateMutex.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCSTR]
            _CreateMutex.restype = wintypes.HANDLE

            _WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
            _WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            _WaitForSingleObject.restype = wintypes.DWORD

            _ReleaseMutex = ctypes.windll.kernel32.ReleaseMutex
            _ReleaseMutex.argtypes = [wintypes.HANDLE]
            _ReleaseMutex.restype = wintypes.BOOL

            _CloseHandle = ctypes.windll.kernel32.CloseHandle
            _CloseHandle.argtypes = [wintypes.HANDLE]
            _CloseHandle.restype = wintypes.BOOL

            INFINITE = 0xFFFFFFFF

            handle = _CreateMutex(None, False, b'global_certifi_win32')
            _WaitForSingleObject(handle, INFINITE)

        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path))
            if sys.platform == 'win32':
                # For each directory in the path (except the root), make sure it is traversable
                # by any local user. Otherwise the PEM file cannot be read.
                p = os.path.abspath(os.path.dirname(path))
                while not re.compile("^\w:\\\\$").match(p):
                    make_world_readable(p, True)
                    p, _ = os.path.split(p)
            elif sys.platform == 'darwin' or sys.platform.startswith('linux'):
                # be careful not change anything else beyond the ancestors of cacert.pem
                pem_path_splits = path.split(os.sep)
                for i in range(len(pem_path_splits)-2):
                    p = os.sep.join(pem_path_splits[0:len(pem_path_splits)-i])
                    os.chmod(p, 0755)

    def generate_pem(self, path):
        self.create_pem_path(path)
        self.add_certifi_pem(path)
        certs = []
        if sys.platform == 'win32':
            certs = self.add_pems_win()
        else: 
            certs = self.get_pems_osx()    
        self.save(certs, path)

        
    def save(self, certs, path):
        import codecs
        with codecs.open(path, 'a', 'utf-8') as f:
            for pem in certs:
                f.write(pem)
           
        if sys.platform == 'win32':
            _ReleaseMutex(handle)
            _CloseHandle(handle)
            make_world_readable(path, False)


    def make_world_readable(fs_object, is_dir):
        try:
            import win32security
            import ntsecuritycon as ntfs

            # Standard Python functions like os.chmod() don't really work with Windows. So if we want
            # files or directories to be accessible for all users, we need to explicitly add an ACL
            # for the "Users" group.
            users, _, _ = win32security.LookupAccountName('', 'USERS')
            sd = win32security.GetFileSecurity(fs_object, win32security.DACL_SECURITY_INFORMATION)
            dacl = sd.GetSecurityDescriptorDacl()
            if is_dir:
                perms = ntfs.FILE_TRAVERSE | ntfs.FILE_LIST_DIRECTORY
            else:
                perms = ntfs.FILE_GENERIC_READ
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, perms, users)
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(fs_object, win32security.DACL_SECURITY_INFORMATION, sd)
        except Exception as e:
            print(sys.stderr, 'Failed to set permissions on %s: %s', fs_object, e)

PEMPATH = ""
if sys.platform == 'win32':
    PEM_PATH = unicode(os.path.join(os.getenv('SystemDrive') + '\\', 'PreVeilData', 'daemon', 'certifi', 'cacert.pem'))
elif sys.platform == 'darwin' or sys.platform.startswith('linux'):
    PEM_PATH = unicode(os.path.join('/var', 'preveil',
                                'daemon', 'certifi', 'cacert.pem'))

  
a = CertificateBundle()
CertificateBundle.generate_pem(a,PEM_PATH)