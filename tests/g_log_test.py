#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cStringIO
import sys

from pvHelpers.logger import g_log

# capture stdout of g_log
stdout_ = sys.stdout
stream = cStringIO.StringIO()
sys.stdout = stream
g_log.exception("debug_msg")
sys.stdout = stdout_  # restore the previous stdout.
msg = stream.getvalue()

# remove the time stamp since we can't capture that
assert " ".join(msg.split(" ")
                [2:]) == "EXCEPTION: (g_log_test.py 12: <module>) debug_msg\n"


def test_g_log_caller_info():
    # capture stdout of g_log
    stdout_ = sys.stdout
    stream = cStringIO.StringIO()
    sys.stdout = stream
    g_log.debug("debug_msg")
    sys.stdout = stdout_  # restore the previous stdout.
    msg = stream.getvalue()

    # remove the time stamp since we can't capture that
    assert " ".join(
        msg.split(" ")[2:]
    ) == "DEBUG: (g_log_test.py 26: test_g_log_caller_info) debug_msg\n"

    def caller():
        stdout_ = sys.stdout
        stream = cStringIO.StringIO()
        sys.stdout = stream
        g_log.info("debug_msg")
        sys.stdout = stdout_  # restore the previous stdout.
        return stream.getvalue()

    assert " ".join(caller().split(" ")
                    [2:]) == "INFO: (g_log_test.py 39: caller) debug_msg\n"

    def caller2():
        def inner_func():
            stdout_ = sys.stdout
            stream = cStringIO.StringIO()
            sys.stdout = stream

            g_log.warn("debug_msg")
            sys.stdout = stdout_  # restore the previous stdout.
            return stream.getvalue()

        return inner_func()

    assert " ".join(caller2().split(" ")
                    [2:]) == "WARN: (g_log_test.py 52: inner_func) debug_msg\n"


def test_utf8_encoding():
    # capture stdout of g_log
    stdout_ = sys.stdout
    stream = cStringIO.StringIO()
    sys.stdout = stream
    g_log.debug('Τη γλώσσα μου έδωσαν ελληνική')
    sys.stdout = stdout_  # restore the previous stdout.
    msg = stream.getvalue()

    # remove the time stamp since we can't capture that
    assert " ".join(
        msg.split(" ")[2:]
    ) == "DEBUG: (g_log_test.py 67: test_utf8_encoding) Τη γλώσσα μου έδωσαν ελληνική\n"
