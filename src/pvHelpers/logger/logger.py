import datetime
import inspect
import logging
import logging.handlers
import os
import types


class LogWrapper(object):
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
                print "{} DEBUG: {} {}".format(self.__now(), caller_info,
                                               string)
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
                print "{} INFO: {} {}".format(self.__now(), caller_info,
                                              string)
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
                print "{} WARN: {} {}".format(self.__now(), caller_info,
                                              string)
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
                print "{} ERROR: {} {}".format(self.__now(), caller_info,
                                               string)
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
                print "{} EXCEPTION: {} {}".format(self.__now(), caller_info,
                                                   exception)
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
            logpath, maxBytes=1000000, backupCount=20)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        self.logobj.addHandler(handler)

        if extra_logger is not None:
            extra_logger.addHandler(handler)

        if twisted_observer_fn is not None:
            observer = twisted_observer_fn(loggerName=name)
            observer.start()


g_log = LogWrapper()
