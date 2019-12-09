from multiprocessing import Array, current_process, Value
import random
import time

from pvHelpers.store import GetDBSession
import semver
import sqlalchemy


def db_writer(flag, result, wd):
    _self = current_process()
    print _self.name
    with result.get_lock():
        # 0 for normal excecution, 1 for locked exception, 2 for other
        result.value = 0
    wd = "".join(wd.value)
    # 1 for mail, 0 for user
    with GetDBSession(wd) as session:
        try:
            # this causes `BEGIN IMMEDIATE`, hence RESERVED LOCK, hench blocks out any other RESERVED lock request
            session.begin()
            # 1 means hold db write lock, 0 releases db write lock
            while flag.value == 1:
                # dummy query just to validate db connection
                mode = session.execute("PRAGMA journal_mode ").fetchone()
                assert mode[0] == u"wal"
                time.sleep(random.random())
        except sqlalchemy.exc.OperationalError as e:
            print e
            with result.get_lock():
                result.value = 1
        except Exception as e:
            print e
            with result.get_lock():
                result.value = 2


def db_reader(flag, result, wd):
    _self = current_process()
    print _self.name
    with result.get_lock():
        # 0 for normal excecution, 1 for locked exception, 2 for other
        result.value = 0
    wd = "".join(wd.value)
    with GetDBSession(wd) as session:
        try:
            # 1 means hold db write lock, 0 releases db write lock
            while flag.value == 1:
                # dummy query just to validate db connection
                session.execute("SELECT * FROM Mailboxes").fetchone()
                mode = session.execute("PRAGMA journal_mode").fetchone()
                assert mode[0] == u"wal"
                time.sleep(random.random())
        except sqlalchemy.exc.OperationalError as e:
            print e
            with result.get_lock():
                result.value = 1
        except Exception as e:
            print e
            with result.get_lock():
                result.value = 2


# class TestHelpers(object):
#     # use this helper to make sure all the subprocesses get terminated in the test's teardown
#     def createProcess(self, *args, **kwargs):
#         np = Process(*args, **kwargs)
#         self.process_pool.append(np)
#         return np

#     def forceTerminateSubProcesses(self):
#         for p in self.process_pool:
#             p.terminate()
#             p.join(timeout=1)

#         time.sleep(0.2)

#         for p in self.process_pool:
#             self.assertFalse(p.is_alive())


# def setUp(self):
#     self.process_pool = []

# def tearDown(self):
#     self.forceTerminateSubProcesses()


# the sqlite3 driver internally shipped w python2.7 mercurial mirror (the blob we currently use) is of version 3.8
# and it apprears to have issues w Sqlite WAL journaling mode. Therefore, we build and ship pysqlite2
# driver as a standalone package, this test will verify that the driver w the desired version has been shipped
# and is being used by the db_store module.
def test_sqlite_driver_version(tmp_factory):
    from . import misc
    # verifying it's been shipped along the python blob
    from pysqlite2 import dbapi2 as _sqlite3

    assert semver.parse_version_info(_sqlite3.version) >= (2, 8, 3)
    assert semver.parse_version_info(_sqlite3.sqlite_version) >= (3, 19)
    # verifying the shipped driver's passing tests
    from pysqlite2 import test
    test_results = test.test()
    assert len(test_results.failures) + len(test_results.errors) == 0

    # verifying that db_store module is using the right driver
    assert GetDBSession.PYSQLITE_VERSION >= (2, 8, 3)
    assert GetDBSession.SQLITE_DRIVER_VERSION >= (3, 19)

    # verifying that provided session/connection is actually bound to the right driver
    with GetDBSession(misc.Config.WORKING_DIR) as session:
        dbapi_driver = session.get_bind().dialect.dbapi
        api_in_use_version = semver.parse_version_info(dbapi_driver.version)
        sqlite_in_use_version = semver.parse_version_info(dbapi_driver.sqlite_version)
        assert api_in_use_version >= (2, 8, 3)
        assert sqlite_in_use_version >= (3, 19)


def test_connection_pooling(tmp_factory):
    with GetDBSession() as session:
        my_connnection = session.get_bind().raw_connection().connection

    for _ in xrange(5):
        with GetDBSession() as session:
            # making sure an open connection is reused and returned by pull
            assert session.get_bind().raw_connection().connection == my_connnection


def test_journal_mode(tmp_factory):
    with GetDBSession() as session:
        assert session.execute("PRAGMA journal_mode").fetchone()[0] == u"wal"

    with GetDBSession() as session:
        assert session.execute("PRAGMA journal_mode").fetchone()[0] == u"wal"


def test_multiple_writer(tmp_factory, create_process):
    writer_1_flag = Value("i", 1)
    writer_1_result = Value("i")
    writer_1_wd = Array("c", str(misc.Config.WORKING_DIR))
    writer_1_process = create_process(
        name="writer_1_process", target=db_writer, args=(writer_1_flag, writer_1_result, writer_1_wd))

    # writer 2
    writer_2_flag = Value("i", 1)
    writer_2_result = Value("i")
    writer_2_process = create_process(
        name="writer_2_process", target=db_writer, args=(writer_2_flag, writer_2_result, writer_1_wd))

    writer_1_process.start()
    # process scheduling is up to operating system, wait so to be certain process_1 starts first
    time.sleep(0.5)
    writer_2_process.start()
    # This process should user it's 5 sec timeout (so waiting around 6 sec for it to join)
    # and then throw (sqlite3.OperationalError) database is locked error => get terminated by SIGTERM
    writer_2_process.join(timeout=6)
    writer_1_flag.value = 0
    time.sleep(0.5)

    assert writer_1_result.value == 0
    assert writer_2_result.value == 1
    writer_1_process.terminate()
    writer_2_process.terminate()


def test_single_writer_multiple_reader(create_process, tmp_factory):
    writer_1_flag = Value("i", 1)
    writer_1_result = Value("i")
    writer_1_wd = Array("c", str(misc.Config.WORKING_DIR))
    writer_1_process = create_process(
        name="writer_1_process", target=db_writer, args=(writer_1_flag, writer_1_result, writer_1_wd))
    writer_1_process.start()

    # let wrtier start fisrt
    time.sleep(0.5)

    reader_processes = {}
    for i in xrange(10):
        reader_flag = Value("i", 1)
        reader_result = Value("i")
        reader_wd = Array("c", str(misc.Config.WORKING_DIR))
        name = "reader_{}_process".format(i)
        reader_processes[i] = {
            "process": create_process(
                name=name, target=db_reader, args=(reader_flag, reader_result, reader_wd)),
            "flag": reader_flag,
            "result": reader_result,
            "name": name
        }

    # start all the readers
    for reader_node in reader_processes.values():
        print "Starting reader {}".format(reader_node["name"])
        reader_node["process"].start()

    # Let processes run for 10 sec
    time.sleep(10)

    # set stop flag
    for reader_node in reader_processes.values():
        reader_node["flag"].value = 0
        reader_node["process"].join(timeout=0.2)
        assert reader_node["process"].terminate() is False
    # assert resutlt value to be normal (0)
    failed = False
    for reader_node in reader_processes.values():
        if reader_node["result"].value != 0:
            failed = True

    # set writer stop flag
    writer_1_flag.value = 0
    writer_1_process.join(0.2)

    # assert succesfull writer
    if writer_1_result.value != 0:
        failed = True

    writer_1_process.terminate()
    assert failed is False
