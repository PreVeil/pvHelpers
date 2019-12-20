import os
import sys

if sys.platform in ["darwin", "linux2"]:
    import pwd


class DoAsPreVeil(object):
    def __init__(self):
        self._noop = True

    def __enter__(self):
        if sys.platform in ["darwin", "linux2"]:
            self.original_egid = os.getegid()
            self.original_euid = os.geteuid()

            preveil_pwuid = pwd.getpwnam("preveil")
            if self.original_egid == preveil_pwuid.pw_gid and   \
                    self.original_euid == preveil_pwuid.pw_uid:
                self._noop = True
                return

            try:
                # seteuid/gid fails unless process is running as `root`
                # Tests do not run as `root`
                os.setegid(preveil_pwuid.pw_gid)
                os.seteuid(preveil_pwuid.pw_uid)
                self._noop = False
            except OSError:
                pass
        else:
            pass

    def __exit__(self, type, value, traceback):
        if sys.platform in ["darwin", "linux2"]:
            if self._noop is False:
                os.setegid(self.original_egid)
                os.seteuid(self.original_euid)
        else:
            pass

        if isinstance(value, Exception):
            raise value


def switch_user_preveil():
    if sys.platform in ["darwin", "linux2"]:
        preveil_pwuid = pwd.getpwnam("preveil")
        os.setregid(preveil_pwuid.pw_gid, preveil_pwuid.pw_gid)
        os.setreuid(preveil_pwuid.pw_uid, preveil_pwuid.pw_uid)
    elif "win32" == sys.platform:
        pass


def check_running_as_root():
    if sys.platform in ["darwin", "linux2"]:
        uid = os.getuid()
        gid = os.getgid()
        if uid != os.geteuid():
            return False
        elif gid != os.getegid():
            return False
        elif uid != 0:
            return False
        elif gid != 0:
            return False
        return True
    else:
        return True
