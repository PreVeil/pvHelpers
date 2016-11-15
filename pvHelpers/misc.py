import os
import yaml
import sys
import random
import time
import simplejson
import datetime
import base64
import logging
import logging.handlers
import sqlite3
import types
import struct

if sys.platform in ["darwin", "linux2"]:
    import pwd
    import grp
else:
    pass

DATA_DIR_MODE = 0o750
HTTP_TIMEOUT = 15

def initRandom():
    seed = struct.unpack('=I', os.urandom(4))[0]
    random.seed(seed)

def getdir(path):
    return os.path.dirname(os.path.realpath(path))

class MetaConf(type):
    @staticmethod
    def determineCurrentMode(mode_file_path):
        if not isinstance(mode_file_path, unicode):
            raise Exception(u"error, determineCurrentMode: mode_file_path must be unicode")

        # Precedence
        # 0. Env[PREVEIL_MODE]
        # 1. conf/default-mode
        # 2. 'dev'
        mode = os.environ.get(u'PREVEIL_MODE')
        if mode != None:
            status, mode = unicodeIfUnicodeElseDecode(mode)
            if status == False:
                raise Exception(u"error, determineCurrentMode: unicodeIfUnicodeElseDecode failed")
            return mode

        try:
            with open(mode_file_path, u'r') as f:
                mode = f.read().strip()
            status, mode = ASCIIToUnicode(mode)
            if status == False:
                raise Exception(u"error, determineCurrentMode: ASCIIToUnicode failed")
            return mode
        except IOError:
            pass

        return u'dev'

    def __init__(cls, name, bases, dct):
        config_dir = dct.get(u"config_dir")
        if not isinstance(config_dir, unicode):
            raise Exception(u"error: MetaConf.config_dir must be unicode")
        mode_file_path = os.path.join(config_dir, u"default-mode")
        config_file_path = os.path.join(config_dir, u"config.yaml")

        cls.mode = MetaConf.determineCurrentMode(mode_file_path)
        cls.data = {}

        try:
            with open(config_file_path, u'r') as f:
                c = yaml.load(f.read())
                if c.has_key(cls.mode) is False:
                    raise Exception(u"error, exiting: PREVEIL_MODE={} unavailable at {}".format(mode, config_file_path))
            cls.data = c
        except IOError:
            pass

        cls.path = config_file_path

        super(MetaConf, cls).__init__(name, bases, dct)

    def _getValue(cls, key, override_mode=None):
        value = os.environ.get(key)
        if value is not None:
            return value

        if override_mode is None:
            override_mode = cls.mode

        if cls.data.has_key(override_mode) == False:
            raise Exception(u"error, exiting: PREVEIL_MODE={} unavailable at {} for key {}".format(override_mode, cls.config_file_path, key))
        value = cls.data[override_mode][key]

        return value

class LogWrapper:
    def __init__(self):
        self.logobj = None

    def updateLog(self, logobj):
        self.logobj = logobj

    def debug(self, string):
        if self.logobj is not None:
            self.logobj.debug(string)
        else:
            print "{} DEBUG: {}".format(self.__now(), string)

    def info(self, string):
        if self.logobj is not None:
            self.logobj.info(string)
        else:
            print "{} INFO: {}".format(self.__now(), string)

    def warning(self, string):
        if self.logobj is not None:
            self.logobj.warning(string)
        else:
            print "{} WARN: {}".format(self.__now(), string)

    warn=warning

    def error(self, string):
        if self.logobj is not None:
            self.logobj.error(string)
        else:
            print "{} ERROR: {}".format(self.__now(), string)

    def __now(self):
        return datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    # We don't start file system writes from the constructor because they
    # depend on the PreVeil directory structure.  Once we've confirmed
    # the PreVeil directories exist, we can start logging to disk instead of
    # stdout.
    def startFileSystemWrites(self, name, twisted_observer_fn=None, extra_logger=None):
        if not isinstance(twisted_observer_fn, types.NoneType):
            if not (callable(twisted_observer_fn) and twisted_observer_fn.__name__ == "PythonLoggingObserver"):
                return False

        self.logobj = logging.getLogger(name)
        self.logobj.setLevel(logging.DEBUG)

        logpath = os.path.join(logsDir(), "{}.log".format(name))
        # TimedRotatingFileHandler will only rotate the logs if the process is
        # running at midnight (assuming a log per day). This means that
        # clients who put their computer to sleep at night will never get a log
        # rotation.  Just use RotatingFileHandler so we can avoid exploded logs.
        handler   = logging.handlers.RotatingFileHandler(logpath, maxBytes=1000000, backupCount=1000)
        formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s,%(lineno)d]: %(message)s')
        handler.setFormatter(formatter)
        self.logobj.addHandler(handler)

        if extra_logger is not None:
            extra_logger.addHandler(handler)

        if twisted_observer_fn is not None:
            observer = twisted_observer_fn(loggerName=name)
            observer.start()

def unicodeToASCII(s):
    if not isinstance(s, unicode):
        return False, None

    try:
        return True, s.encode('ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False, False

def unicodeToASCIIWithReplace(s):
    return s.encode('ascii', 'replace')

def ASCIIToUnicode(s):
    if not isinstance(s, str):
        return False, None

    try:
        return True, s.encode('utf-8').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False, False

def utf8Encode(s):
    if not isinstance(s, unicode):
        return False, None

    try:
        return True, s.encode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False, False

def utf8Decode(s):
    if not (isinstance(s, str) or isinstance(s, bytes)):
        return False, None

    try:
        return True, s.decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False, False

def unicodeIfUnicodeElseDecode(b):
    if isinstance(b, unicode):
        return True, b
    else:
        return utf8Decode(b)

# binary -> unicode
def b64enc(data, altchars=None):
    if not (isinstance(data, bytes) or isinstance(data, str)):
        return False, None

    enc = base64.b64encode(data, altchars=altchars)
    return ASCIIToUnicode(enc)

# unicode -> binary
def b64dec(data, altchars=None):
    if not isinstance(data, unicode):
        return False, None

    try:
        return True, base64.b64decode(data, altchars=altchars)
    except TypeError:
        return False, None

def toInt(data):
    if not (isinstance(data, unicode) or (isinstance(data, (int, long, float)))):
        return False, None

    try:
        return True, int(data)
    except ValueError:
        return False, None

def jdumps(data, ensure_ascii=False):
    return simplejson.dumps(data, ensure_ascii=ensure_ascii)

def jloads(data):
    if not isinstance(data, unicode):
        return False, None

    try:
        return True, simplejson.loads(data)
    except (simplejson.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError, ValueError):
        return False, None

def jload(fp):
    if not isinstance(fp, file):
        return False, None

    try:
        return True, simplejson.load(fp)
    except (simplejson.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError, ValueError):
        return False, None

def filesystemSafeBase64Encode(email):
    return b64enc(email.upper(), "()")

def getTempFilePath():
    return os.path.join(tempDir(),
        "%s.%s.%s" % (time.time(), random.randint(0, 1000000), os.getpid()))

def getBodyFromFlankerMessage(message, flanker_from_string):
    if not (callable(flanker_from_string) and flanker_from_string.__name__ == "from_string"):
        return False, None

    if message.content_type.is_singlepart():
        return True, message._container.read_body()
    elif message.content_type.is_multipart():
        # HACK: Print message text without the headers
        tmp = flanker_from_string(message.to_string())
        tmp.remove_headers(*tmp.headers.keys())
        return True, tmp.to_string()
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

class DoAsPreVeil:
    def __init__(self):
        pass

    def __enter__(self):
        if sys.platform in ["darwin", "linux2"]:
            self.original_egid = os.getegid()
            self.original_euid = os.geteuid()

            preveil_pwuid = pwd.getpwnam("preveil")
            if self.original_egid == preveil_pwuid.pw_gid and   \
                    self.original_euid == preveil_pwuid.pw_uid:
                self.noop = True
                return

            self.noop = False
            os.setegid(preveil_pwuid.pw_gid)
            os.seteuid(preveil_pwuid.pw_uid)
        else:
            pass

    def __exit__(self, type, value, traceback):
        if sys.platform in ["darwin", "linux2"]:
            if self.noop is False:
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
    directory = os.path.join(directory, '')

    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([test_child, directory]) == directory

def recur_chown(path, uid, gid):
    for root, dirs, files in os.walk(path):
        for name in dirs:
            os.chown(os.path.join(root, name), uid, gid)
        for name in files:
            os.chown(os.path.join(root, name), uid, gid)

def quiet_mkdir(path):
    try:
        os.mkdir(path)
    except OSError:
        if not os.path.isdir(path):
            raise

def quietMakedirsInPreVeilDataDir(path):
    if isSameDirOrChild(preveilDataDir(), path) is False:
        raise Exception("path is not in data dir: %s" % path)

    with DoAsPreVeil() as _:
        if sys.platform in ["darwin", "linux2"]:
            mask = os.umask(0o777)
            os.umask(mask)
            if (DATA_DIR_MODE & (~ mask)) != DATA_DIR_MODE:
                raise Exception("bad umask: %s" % mask)
        else:
            pass

        try:
            os.makedirs(path, DATA_DIR_MODE)
        except OSError:
            if not os.path.isdir(path):
                raise

def quietMkdirInPreVeilDataDir(path):
    if isSameDirOrChild(preveilDataDir(), path) is False:
        raise Exception("path is not in data dir: %s" % path)

    with DoAsPreVeil() as _:
        if sys.platform in ["darwin", "linux2"]:
            mask = os.umask(0o777)
            os.umask(mask)
            if (DATA_DIR_MODE & (~ mask)) != DATA_DIR_MODE:
                raise Exception("bad umask: %s" % mask)
        else:
            pass

        try:
            os.mkdir(path, DATA_DIR_MODE)
        except OSError:
            if not os.path.isdir(path):
                raise

def file_no_ext(path):
    return os.path.splitext(os.path.basename(path))[0]

def preveilDataDir():
    if sys.platform in ["darwin", "linux2"]:
        return os.path.join("/", "var", "preveil")
    elif "win32" == sys.platform:
        return os.path.join(os.getenv("SystemDrive") + "\\", "PreVeilData")
    else:
        raise Exception("preveilDataDir: Unsupported platform")

def daemonDataDir():
    return os.path.join(preveilDataDir(), "daemon")

def logsDir():
    return os.path.join(daemonDataDir(), "logs")

def tempDir():
    return os.path.join(daemonDataDir(), "temp")

def modesDir():
    return os.path.join(daemonDataDir(), "modes")

def getModeDir(mode):
    return os.path.join(modesDir(), mode)

# Handle cases where /var/preveil/* doesn't exist or it has the wrong
# owner:group
#
# This function tries to provide the following guarentee, if a process returns
# successfully from initDaemonDataDirs(), /var/preveil/* is available to it with the
# correct owner:group.  This guarentee is easier to provide if all processes
# only create these directories (or change their permissions) with this
# function.
def initDaemonDataDirs(mode):
    if sys.platform in ["darwin", "linux2"]:
        mask = os.umask(0o777)
        os.umask(mask)
        if (DATA_DIR_MODE & (~ mask)) != DATA_DIR_MODE:
            raise Exception("bad umask: %s" % mask)
    else:
        pass

    quiet_mkdir(preveilDataDir())
    quiet_mkdir(daemonDataDir())
    quiet_mkdir(logsDir())
    quiet_mkdir(tempDir())
    quiet_mkdir(modesDir())
    quiet_mkdir(getModeDir(mode))

    preveil_pwuid = pwd.getpwnam("preveil")
    preveil_uid = preveil_pwuid.pw_uid
    preveil_gid = preveil_pwuid.pw_gid

    recur_chown(preveilDataDir(), preveil_uid, preveil_gid)

# Lifted from m000 @ http://stackoverflow.com/a/32888599
class CaseInsensitiveDict(dict):
    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, basestring) else key
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
