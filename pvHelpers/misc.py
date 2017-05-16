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
import types
import struct
import collections
import copy

from sqlalchemy import create_engine, event, orm

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

def resolvePreVeilMode(mode_file_path):
    if not isinstance(mode_file_path, unicode):
        print u"error, determineCurrentMode: mode_file_path must be unicode"
        return False, None

    # Precedence
    # 0. Env[PREVEIL_MODE]
    # 1. conf/default-mode
    # 2. 'dev'
    mode = os.environ.get(u'PREVEIL_MODE')
    if mode != None:
        status, mode = unicodeIfUnicodeElseDecode(mode)
        if status == False:
            print u"error, determineCurrentMode: unicodeIfUnicodeElseDecode failed"
            return False, None
        return True, mode

    try:
        with open(mode_file_path, u'r') as f:
            mode = f.read().strip()
        status, mode = ASCIIToUnicode(mode)
        if status == False:
            print u"error, determineCurrentMode: ASCIIToUnicode failed"
        return True, mode
    except IOError:
        pass

    return True, u'dev'

def readYAMLConfig(path):
    if not isinstance(path, unicode):
        return False, None

    try:
        with open(path, u'r') as f:
            c = yaml.load(f.read())
            return True, c
    except IOError as e:
        return False, None

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

# FIXME: Do we need to handle more "events" in order to get DDL queries
#        to work in SAVEPOINTs.
class GetUserDBSessionAsPreVeil(DoAsPreVeil):
    def __init__(self, mode):
        DoAsPreVeil.__init__(self)
        self.mode = mode

    __engines = {}
    @classmethod
    def getSessionMaker(cls, mode):
        value = cls.__engines.get(mode, None)
        if value != None:
            (engine, session_maker) = value
            return session_maker

        engine = create_engine('sqlite:///{}'.format(getUserDatabasePath(mode)))
        # HACK: source, http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#pysqlite-serializable
        # Let's use use DDL queries in transactions.
        @event.listens_for(engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None
            dbapi_connection.execute('PRAGMA fullfsync = 1')
        @event.listens_for(engine, "begin")
        def do_begin(conn):
            # emit our own BEGIN
            conn.execute("BEGIN IMMEDIATE")

        session_maker = orm.session.sessionmaker(bind=engine, autocommit=True)
        cls.__engines[mode] = (engine, session_maker)
        return session_maker

    def __enter__(self):
        DoAsPreVeil.__enter__(self)

        self.session = self.getSessionMaker(self.mode)()
        return self.session

    def __exit__(self, type, value, traceback):
        self.session.close()

        DoAsPreVeil.__exit__(self, type, value, traceback)

class GetMailDBSessionAsPreVeil(DoAsPreVeil):
    def __init__(self, mode):
        DoAsPreVeil.__init__(self)
        self.mode = mode

    __engines = {}
    @classmethod
    def getSessionMaker(cls, mode):
        value = cls.__engines.get(mode, None)
        if value != None:
            (engine, session_maker) = value
            return session_maker

        engine = create_engine('sqlite:///{}'.format(getMailDatabasePath(mode)))
        # HACK: source, http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#pysqlite-serializable
        # Let's use use DDL queries in transactions.
        @event.listens_for(engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None
            dbapi_connection.execute('PRAGMA fullfsync = 1')
        @event.listens_for(engine, "begin")
        def do_begin(conn):
            # emit our own BEGIN
            conn.execute("BEGIN IMMEDIATE")
        session_maker = orm.session.sessionmaker(bind=engine, autocommit=True)
        cls.__engines[mode] = (engine, session_maker)
        return session_maker

    def __enter__(self):
        DoAsPreVeil.__enter__(self)

        self.session = self.getSessionMaker(self.mode)()
        return self.session

    def __exit__(self, type, value, traceback):
        self.session.close()

        DoAsPreVeil.__exit__(self, type, value, traceback)

class UserDBNode:
    @staticmethod
    def new(user_id, display_name, mail_cid, password):
        if not isinstance(user_id, unicode):
            return False, None
        if not isinstance(display_name, unicode):
            return False, None
        if not isinstance(mail_cid, unicode):
            return False, None
        if not isinstance(password, unicode):
            return False, None

        return True, UserDBNode(user_id, display_name, mail_cid, password)

    def __init__(self, user_id, display_name, mail_cid, password):
        self.user_id = user_id
        self.display_name = display_name
        self.mail_cid = mail_cid
        self.password = password

    def toDict(self):
        return {
            "user_id" : self.user_id,
            "display_name" : self.display_name,
            "mail_cid" : self.mail_cid,
            "password" : self.password
        }

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
    os.chown(path, uid, gid)
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

def getUserDatabasePath(mode):
    return os.path.join(getModeDir(mode), "user_db.sqlite")

def getMailDatabasePath(mode):
    return os.path.join(getModeDir(mode), "db.sqlite")

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

    if sys.platform in ["darwin", "linux2"]:
        preveil_pwuid = pwd.getpwnam("preveil")
        preveil_uid = preveil_pwuid.pw_uid
        preveil_gid = preveil_pwuid.pw_gid
        recur_chown(preveilDataDir(), preveil_uid, preveil_gid)
    else:
        pass

class CaseInsensitiveSet(collections.Set):
    def __init__(self, lyst):
        self.data  = dict()
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
        if type(other) != list:
            util.logRaise("bad type")
        new = copy.deepcopy(self.data)
        for o in other:
            new[o.upper()] = o

        return CaseInsensitiveSet(new.values())

    def difference(self, other):
        if type(other) != list:
            util.logRaise("bad type")
        new = copy.deepcopy(self.data)
        for o in other:
            if o.upper() in new:
                del new[o.upper()]

        return CaseInsensitiveSet(new.values())

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
