import os
import types

import semver
from pysqlite2 import dbapi2 as sqlite3
from sqlalchemy import create_engine, event, exc, orm
from sqlalchemy.pool import SingletonThreadPool

from pvHelpers.utils import DoAsPreVeil


class GetDBSession(object):
    DRIVER = sqlite3
    PYSQLITE_VERSION = semver.parse_version_info(sqlite3.version)
    SQLITE_DRIVER_VERSION = semver.parse_version_info(sqlite3.sqlite_version)
    __session_factory = {}

    def __init__(self, path):
        self.path = path
        self.session = None

    @classmethod
    def getSession(cls, path):
        # creating new DB session factory, binding it to an engine and a connection pool
        if path not in cls.__session_factory:
            # using SingltonThreadPool so to maintain the connection instead of recreating one per transaction
            # Explicitly using standalone pysqlite2 driver instead of the built-in pysqlite driver
            engine = create_engine("sqlite+pysqlite:///{}".format(path), poolclass=SingletonThreadPool, module=cls.DRIVER)

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
            # cls.__session_factory[path]["factory"]().execute("select * from store")

        return cls.__session_factory[path]["factory"]()

    def __enter__(self):
        self.session = self.getSession(self.path)
        return self.session

    def __exit__(self, type_, value, traceback):
        if self.session:
            self.session.close()


class DBException(Exception):
    def __init__(self, message=""):
        super(DBException, self).__init__(message)


# TODO: be more specific on these errors, i.e. :
# no need to retry on NoSuchColumnError, while can retry on TimeoutError
DBRetryableErrors = [exc.SQLAlchemyError]