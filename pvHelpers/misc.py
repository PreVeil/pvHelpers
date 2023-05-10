import base64
import collections
import copy
import datetime
import inspect
import itertools
import logging
import logging.handlers
import os
import random
import StringIO
import struct
import sys
import time
import types
import urllib

import requests
import simplejson
import urlparse
import yaml
from sqlalchemy import create_engine, event, orm

from .hook_decorators import WrapExceptions
from .params import params

DATA_DIR_MODE = 0o750
HTTP_TIMEOUT = 15


class EncodingException(Exception):
    def __init__(self, exception=u""):
        super(EncodingException, self).__init__(exception)


class __NOOPAuth(requests.auth.AuthBase):
    def __call__(self, r):
        return r


NOOPAuth = __NOOPAuth()

if sys.platform in ["darwin", "linux2"]:
    import pwd
    import grp
else:
    pass


def initRandom():
    seed = struct.unpack("=I", os.urandom(4))[0]
    random.seed(seed)


def getdir(path):
    return os.path.dirname(os.path.realpath(path))


def resolvePreVeilMode(mode_file_path):
    if not isinstance(mode_file_path, unicode):
        g_log.error(u"resolvePreVeilMode: mode_file_path must be unicode")
        return False, None

    # Precedence
    # 0. Env[PREVEIL_MODE]
    # 1. conf/default-mode
    # 2. 'dev'
    mode = os.environ.get(u"PREVEIL_MODE")
    if mode is not None:
        mode = unicodeIfUnicodeElseDecode(mode)
        return True, mode

    try:
        with open(mode_file_path, u"r") as f:
            mode = f.read().strip()
        mode = ASCIIToUnicode(mode)
        return True, mode
    except IOError:
        pass

    return True, u"dev"


def readYAMLConfig(path):
    if not isinstance(path, unicode):
        return False, None

    try:
        with open(path, u"r") as f:
            c = yaml.load(f.read(), Loader=yaml.FullLoader)
            return True, c
    except IOError:
        return False, None


def print_wrapper(msg):
    try:
        print msg
    except IOError:
        return


class _LogWrapper(object):
    def __init__(self):
        self.logobj = None

    def updateLog(self, logobj):
        self.logobj = logobj

    def debug(self, string):
        curframe, calframe = None, None
        try:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            caller_info = self.__format_caller_info(calframe)
            if self.logobj is not None:
                self.logobj.debug(" ".join([caller_info, "%s" % string]))
            else:
                print_wrapper("{} DEBUG: {} {}".format(self.__now(), caller_info, string))
        finally:
            del curframe
            del calframe

    def info(self, string):
        curframe, calframe = None, None
        try:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            caller_info = self.__format_caller_info(calframe)
            if self.logobj is not None:
                self.logobj.info(" ".join([caller_info, "%s" % string]))
            else:
                print_wrapper("{} INFO: {} {}".format(self.__now(), caller_info, string))
        finally:
            del curframe
            del calframe

    def warning(self, string):
        curframe, calframe = None, None
        try:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            caller_info = self.__format_caller_info(calframe)
            if self.logobj is not None:
                self.logobj.warning(" ".join([caller_info, "%s" % string]))
            else:
                print_wrapper("{} WARN: {} {}".format(self.__now(), caller_info, string))
        finally:
            del curframe
            del calframe

    warn = warning

    def error(self, string):
        curframe, calframe = None, None
        try:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            caller_info = self.__format_caller_info(calframe)
            if self.logobj is not None:
                self.logobj.error(" ".join([caller_info, "%s" % string]))
            else:
                print_wrapper("{} ERROR: {} {}".format(self.__now(), caller_info, string))
        finally:
            del curframe
            del calframe

    def exception(self, exception):
        curframe, calframe = None, None
        try:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            caller_info = self.__format_caller_info(calframe)
            if self.logobj is not None:
                self.logobj.exception(" ".join([caller_info,
                                                "%s" % exception]))
            else:
                print_wrapper("{} EXCEPTION: {} {}".format(self.__now(), caller_info, exception))
        finally:
            del curframe
            del calframe

    def __now(self):
        return datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def __format_caller_info(self, calframe):
        """
            :return: (filename, line_number, func)
            Note: calframe[1] should always exist since we call inspect within one of the log print
            methods. And the log print method is called from a daemon's context somewhere.
        """
        filename = calframe[1][1]
        line_number = calframe[1][2]
        caller_func = calframe[1][3]
        return "({} {}: {})".format(
            filename.split(os.sep)[-1], line_number, caller_func)

    # We don't start file system writes from the constructor because they
    # depend on the PreVeil directory structure.  Once we've confirmed
    # the PreVeil directories exist, we can start logging to disk instead of
    # stdout.
    # <mode> only determines the application directory to use, `PreVeilData` or `PreVeilBleedData`
    def startFileSystemWrites(self,
                              name,
                              log_dir,
                              twisted_observer_fn=None,
                              extra_logger=None):
        if not isinstance(twisted_observer_fn, types.NoneType):
            if not (callable(twisted_observer_fn) and
                    twisted_observer_fn.__name__ == "PythonLoggingObserver"):
                return False

        self.logobj = logging.getLogger(name)
        self.logobj.setLevel(logging.DEBUG)

        logpath = os.path.join(log_dir, "{}.log".format(name))
        # TimedRotatingFileHandler will only rotate the logs if the process is
        # running at midnight (assuming a log per day). This means that
        # clients who put their computer to sleep at night will never get a log
        # rotation. Just use RotatingFileHandler so we can avoid exploded logs.
        handler = logging.handlers.RotatingFileHandler(
            logpath, maxBytes=5000000, backupCount=20)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        self.logobj.addHandler(handler)

        if extra_logger is not None:
            extra_logger.addHandler(handler)

        if twisted_observer_fn is not None:
            observer = twisted_observer_fn(loggerName=name)
            observer.start()


g_log = _LogWrapper()


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode)
def unicodeToASCII(s):
    return s.encode("ascii")


def unicodeToASCIIWithReplace(s):
    return s.encode("ascii", "replace")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes)
def ASCIIToUnicode(s):
    return s.encode("utf-8").decode("utf-8")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode)
def utf8Encode(s):
    return s.encode("utf-8")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes)
def utf8Decode(s):
    return s.decode("utf-8")


def unicodeIfUnicodeElseDecode(b):
    if isinstance(b, unicode):
        return b
    else:
        return utf8Decode(b)


def encodeContentIfUnicode(content):
    if isinstance(content, unicode):
        return utf8Encode(content)
    return content


@WrapExceptions(
    EncodingException,
    [ValueError, KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes, {types.NoneType, str})
def b64enc(data, altchars=None):
    enc = base64.b64encode(data, altchars=altchars)
    return ASCIIToUnicode(enc)


@WrapExceptions(
    EncodingException,
    [ValueError, KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode, {types.NoneType, str})
def b64dec(data, altchars=None):
    return base64.b64decode(data, altchars=altchars)


def toInt(data):
    if not (isinstance(data,
                       (unicode, str)) or (isinstance(data,
                                                      (int, long, float)))):
        return False, None

    try:
        return True, int(data)
    except ValueError:
        return False, None


@WrapExceptions(EncodingException, [UnicodeDecodeError, UnicodeEncodeError])
def jdumps(data, ensure_ascii=False):
    return simplejson.dumps(data, ensure_ascii=ensure_ascii)


@WrapExceptions(EncodingException, [
    KeyError, TypeError, ValueError, simplejson.JSONDecodeError,
    UnicodeDecodeError, UnicodeEncodeError
])
@params(unicode)
def jloads(data):
    return simplejson.loads(data)


def jload(fp):
    if not isinstance(fp, file):
        return False, None

    try:
        return True, simplejson.load(fp)
    except (simplejson.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError,
            ValueError):
        return False, None


def getTempFilePath(mode_dir):
    return os.path.join(
        tempDir(mode_dir),
        "%s.%s.%s" % (time.time(), random.randint(0, 1000000), os.getpid()))


def getBodyFromFlankerMessage(message, flanker_from_string):
    if not (callable(flanker_from_string)
            and flanker_from_string.__name__ == "from_string"):
        return False, None

    if message.content_type.is_singlepart():
        return True, message._container.read_body()
    elif message.content_type.is_multipart():
        # HACK: Print message text without the headers
        tmp = flanker_from_string(message.to_string())
        tmp.remove_headers(*tmp.headers.keys())
        return True, tmp.to_string()
    elif message.content_type.is_message_container():
        return True, message.enclosed.to_string()
    else:
        return False, None


def checkRunningAsRoot():
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
            except OSError as e:
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


def switchUserPreVeil():
    if sys.platform in ["darwin", "linux2"]:
        preveil_pwuid = pwd.getpwnam("preveil")
        os.setregid(preveil_pwuid.pw_gid, preveil_pwuid.pw_gid)
        os.setreuid(preveil_pwuid.pw_uid, preveil_pwuid.pw_uid)
    elif "win32" == sys.platform:
        pass


# lifted from: http://stackoverflow.com/questions/3812849/how-to-check-whether-a-directory-is-a-sub-directory-of-another-directory
def isSameDirOrChild(directory, test_child):
    directory = os.path.normpath(os.path.realpath(directory))
    test_child = os.path.normpath(os.path.realpath(test_child))
    if directory == test_child:
        return True

    # os.path.join, appending nothing adds a trailing seperator;
    # we want to avoid issues like, /a/b matching as the parent of
    # /a/bee/c
    directory = os.path.join(directory, "")

    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([test_child, directory]) == directory


def recur_chown(path, uid, gid):
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for name in dirs:
            os.chown(os.path.join(root, name), uid, gid)
        for name in files:
            os.chown(os.path.join(root, name), uid, gid)


def quiet_mkdir(path):
    # dropping to win32 for Windows
    # python modifies the permissions on Windows folders being created to be too permissive so we manually specify security info
    if sys.platform == "win32":
        import pywintypes
        import win32file
        import win32security
        try:
            """
            Owner            :
            Group            :
            DiscretionaryAcl : {NT AUTHORITY\SYSTEM: AccessAllowed (GenericAll), BUILTIN\Administrators: AccessAllowed (GenericAll)}
            SystemAcl        : {}
            RawDescriptor    : System.Security.AccessControl.CommonSecurityDescriptor
            """
            sddl = "D:PAI(A;OICI;GA;;;SY)(A;OICI;GA;;;BA)"
            sec_descriptor = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(sddl, win32security.SDDL_REVISION_1)
            sec_attributes = win32security.SECURITY_ATTRIBUTES()
            sec_attributes.SECURITY_DESCRIPTOR = sec_descriptor
            win32file.CreateDirectory(path, sec_attributes)
        except pywintypes.error:
            if not os.path.isdir(path):
                raise
    else:
        try:
            os.mkdir(path)
        except OSError:
            if not os.path.isdir(path):
                raise


def file_no_ext(path):
    return os.path.splitext(os.path.basename(path))[0]


def daemonDataDir(wd):
    return os.path.join(wd, "daemon")


def modesDir(wd):
    return os.path.join(daemonDataDir(wd), "modes")


def getModeDir(wd, mode):
    return os.path.join(modesDir(wd), mode)


def logsDir(mode_dir):
    return os.path.join(mode_dir, "logs")


def tempDir(mode_dir):
    return os.path.join(mode_dir, "temp")


def getUserDatabasePath(mode_dir):
    return os.path.join(mode_dir, "user_db.sqlite")


def getMailDatabasePath(mode_dir):
    return os.path.join(mode_dir, "db.sqlite")


def getActionsDatabasePath(mode_dir):
    return os.path.join(mode_dir, "actions_db.sqlite")


# Handle cases where /var/preveil/* doesn't exist or it has the wrong
# owner:group
#
# This function tries to provide the following guarentee, if a process returns
# successfully from initDaemonDataDirs(), /var/preveil/* is available to it with the
# correct owner:group.  This guarentee is easier to provide if all processes
# only create these directories (or change their permissions) with this
# function.
def initDaemonDataDirs(wd, mode, is_test=False):
    if sys.platform in ["darwin", "linux2"]:
        mask = os.umask(0o777)
        os.umask(mask)
        if (DATA_DIR_MODE & (~mask)) != DATA_DIR_MODE:
            raise Exception("bad umask: %s" % mask)
    else:
        pass

    quiet_mkdir(wd)
    quiet_mkdir(daemonDataDir(wd))
    quiet_mkdir(modesDir(wd))
    mode_dir = getModeDir(wd, mode)
    quiet_mkdir(mode_dir)
    quiet_mkdir(logsDir(mode_dir))
    quiet_mkdir(tempDir(mode_dir))

    if not is_test:
        if sys.platform in ["darwin", "linux2"]:
            preveil_uid = pwd.getpwnam("preveil").pw_uid
            preveil_gid = grp.getgrnam("preveil").gr_gid
            os.chown(wd, preveil_uid, preveil_gid)
            recur_chown(daemonDataDir(wd), preveil_uid, preveil_gid)
        else:
            pass

    return mode_dir


class CaseInsensitiveSet(collections.Set):
    def __init__(self, lyst):
        self.data = dict()
        for e in lyst:
            self.data[e.upper()] = e

    def __contains__(self, item):
        return item.upper() in self.data

    def __iter__(self):
        for _, n in self.data.iteritems():
            yield n

    def __len__(self):
        return len(self.data)

    def union(self, other):
        if not isinstance(other, list):
            g_log.error(u"other must be of type list")
            raise TypeError(u"other must be of type list")
        new = copy.deepcopy(self.data)
        for o in other:
            new[o.upper()] = o

        return CaseInsensitiveSet(new.values())

    def difference(self, other):
        if not isinstance(other, list):
            g_log.error(u"other must be of type list")
            raise TypeError(u"other must be of type list")
        new = copy.deepcopy(self.data)
        for o in other:
            if o.upper() in new:
                del new[o.upper()]

        return CaseInsensitiveSet(new.values())


# Lifted from m000 @ http://stackoverflow.com/a/32888599
class CaseInsensitiveDict(dict):
    @classmethod
    def _k(cls, key):
        if isinstance(key, basestring):
            return key.lower()
        elif isinstance(key, tuple):
            return tuple([cls._k(i) for i in key])
        else:
            return key

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(self.__class__._k(key))

    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(self.__class__._k(key), value)

    def __delitem__(self, key):
        return super(CaseInsensitiveDict, self).__delitem__(self.__class__._k(key))

    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(self.__class__._k(key))

    def has_key(self, key):
        return super(CaseInsensitiveDict, self).has_key(self.__class__._k(key))

    def pop(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)

    def update(self, E={}, **F):
        super(CaseInsensitiveDict, self).update(self.__class__(E))
        super(CaseInsensitiveDict, self).update(self.__class__(**F))

    def _convert_keys(self):
        for k in list(self.keys()):
            v = super(CaseInsensitiveDict, self).pop(k)
            self.__setitem__(k, v)


class NOT_ASSIGNED(object):
    def __init__(self):
        pass

    def __str__(self):
        return u"__NOT_ASSIGNED__"

    def serialize(self):
        return self.__str__()


def MergeDicts(*args):
    ret = {}
    for _dict in args:
        if not isinstance(_dict, dict):
            raise TypeError(u"MergeDicts: Arguments must be of type dict")
        ret.update(_dict)
    return ret


def randUnicode(length=20):
    GLYPHS = u"ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz"
    return u"".join(random.choice(GLYPHS) for _ in range(length))


def randStr(size=1024):
    return os.urandom(size)


def randStream(size=1024):
    return StringIO.StringIO(randStr(size))


# https://docs.python.org/dev/library/itertools.html#itertools-recipes
def partition(pred, iterable):
    'Use a predicate to partition entries into false entries and true entries'
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = itertools.tee(iterable)
    return filter(pred, t2), filter(lambda x: not pred(x), t1)


def parse_file_uri(path):
    """
        Process the given path url to determine the scheme.
        :return: required_download, processed_url
    """
    p = urlparse.urlparse(path)

    if p.scheme in ["https", "http"]:
        return True, path
    elif p.scheme == "file":
        # url to path name, i.e: convert %20 to space
        path = urllib.url2pathname(p.path)
        return False, os.path.abspath(os.path.join(p.netloc, path))
    else:
        # treat as a local file
        return False, urllib.unquote(path)
