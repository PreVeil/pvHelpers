import types
from . import misc
from sqlalchemy import create_engine, event, orm
from sqlalchemy.pool import SingletonThreadPool

# Model for User Bucket protocol_version=0
class UserDBNode(object):
    @staticmethod
    def new(user_id, display_name, mail_cid, password, org_id, org_meta):
        if not isinstance(user_id, unicode):
            return False, None
        if not isinstance(display_name, unicode):
            return False, None
        if not isinstance(mail_cid, unicode):
            return False, None
        if not isinstance(password, unicode):
            return False, None
        if not isinstance(org_id, (types.NoneType, unicode)):
            return False,None
        if not isinstance(org_meta, (types.NoneType, dict)):
            return False, None

        return True, UserDBNode(user_id, display_name, mail_cid, password, org_id, org_meta)

    def __init__(self, user_id, display_name, mail_cid, password, org_id, org_meta):
        self.user_id = user_id
        self.display_name = display_name
        self.mail_cid = mail_cid
        self.password = password
        self.org_id = org_id
        self.org_metadata = org_meta

    def toDict(self):
        return {
            "user_id" : self.user_id,
            "display_name" : self.display_name,
            "mail_cid" : self.mail_cid,
            "password" : self.password,
            "org_id" : self.org_id,
            "org_metadata" : self.org_metadata
        }

class GetDBSessionAsPreVeil(misc.DoAsPreVeil):
    def __init__(self, path):
        super(GetDBSessionAsPreVeil, self).__init__()
        self.db_path = path
        self.session = None

    __session_factory = {}

    @classmethod
    def getSession(cls, path):
        # creating new DB session factory, binding it to an engine and a connection pool
        if path not in cls.__session_factory:
            # using SingltonThreadPool so to maintain the connection instead of recreating one per transaction
            engine = create_engine(path, poolclass=SingletonThreadPool)

            # HACK: source, http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#pysqlite-serializable
            # Let's use use DDL queries in transactions.
            # This will get called once per thread (we use one connection per thread)
            @event.listens_for(engine, "connect")
            def do_connect(dbapi_connection, connection_record):
                # disable pysqlite's emitting of the BEGIN statement entirely.
                # also stops it from emitting COMMIT before any DDL.
                dbapi_connection.isolation_level = None

                # fullfsync will enforce use of F_FULLFSYNC on darwin
                dbapi_connection.execute("PRAGMA fullfsync = 1")

                # Setting the DB journal mode to WAL, this will enable coexisint of N readers connection with 1 writer connection
                # This implies that even the readers have to have write privilage to open the DB
                # TODO: tune autocheckpoint number of pages. the default 1000 pages or ~4Mbs
                dbapi_connection.execute("PRAGMA journal_mode = wal")

                # Explicitly setting timeout to wait and retry on SQLITE_LOCKED/BUSY errors
                # TODO: this wait is a thread blokcing wait that is not monkey_patched,
                # thus other server reqs will get blocked as well, devise a non-blocking wait
                dbapi_connection.execute("PRAGMA busy_timeout = 5000")

            # event handler when you call connection/session.begin()
            @event.listens_for(engine, "begin")
            def do_begin(conn):
                # emit our own BEGIN IMMEDIATE, resulting in acquisition of a RESERVED lock on db
                # if acquired, will stop any other connection from acquiring RESERVED/PENDING/EXCLUSIVE LOCK
                # if failed, will throw SQLITE_LOCKED error after busy_timeout (5000 by default)
                conn.execute("BEGIN IMMEDIATE")

            # autocommit=True will let developer to begin() a transaction manually
            # have to be deliberate with begin()/ commit() when doing DDL transactions
            cls.__session_factory[path] = {"engine": engine, "factory": orm.session.sessionmaker(bind=engine, autocommit=True)}

        return cls.__session_factory[path]["factory"]()

    def __enter__(self):
        super(GetDBSessionAsPreVeil, self).__enter__()
        self.session = self.getSession(self.db_path)
        return self.session

    def __exit__(self, type, value, traceback):
        if self.session:
            self.session.close()
        super(GetDBSessionAsPreVeil, self).__exit__(type, value, traceback)

class GetMailDBSessionAsPreVeil(GetDBSessionAsPreVeil):
    def __init__(self, mode):
        self.mode = mode
        super(GetMailDBSessionAsPreVeil, self).__init__("sqlite:///{}".format(misc.getMailDatabasePath(mode)))

class GetUserDBSessionAsPreVeil(GetDBSessionAsPreVeil):
    def __init__(self, mode):
        self.mode = mode
        super(GetUserDBSessionAsPreVeil, self).__init__("sqlite:///{}".format(misc.getUserDatabasePath(mode)))
