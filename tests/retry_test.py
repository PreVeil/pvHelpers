import time

from pvHelpers.utils.retry import retry, RetryError
import pytest
import requests
import sqlalchemy


class DummyCount:
    def __init__(self):
        self.call_count = 0


class DummyException(Exception):
    def __init__(self, message):
        super(DummyException, self).__init__(message)


# Makes functions that raise the exceptions in the provided order.
# returns successfully on call number: ${len(raises)}
# This is just to emulate possible occurence of exceptions in the wrapped functions
def function_maker(raises=[]):
    c = DummyCount()

    def dummy_func(*args, **kwargs):
        if c.call_count >= len(raises):
            return u"success, positional args: {}, named args: {}".format(list(args), kwargs)

        c.call_count += 1
        raise raises[c.call_count-1]("raising on dummy call {}".format(c.call_count-1))

    return dummy_func


def test_failing_retry():
    raising_exceptions = [Exception, requests.exceptions.RequestException]
    try_count = 2
    func = function_maker(raises=raising_exceptions)

    with pytest.raises(RetryError) as exc:
        retry(func, count=try_count)

    # messages are important, so not to loose trace of what has happened internal to the retry wrapper
    assert exc.value.message == \
        u"Function failed {} times throwing {}".format(
            try_count,
            [(e, "raising on dummy call {}".format(i)) for i, e in enumerate(raising_exceptions[:try_count])])


def test_retry_with_unexpected_exception():
    raising_exceptions = [requests.exceptions.RequestException, sqlalchemy.exc.SQLAlchemyError]
    func = function_maker(raises=raising_exceptions)
    try_count = 3

    with pytest.raises(Exception) as e:
        retry(func, exceptions=raising_exceptions[:1], count=try_count)
    assert isinstance(e.value, sqlalchemy.exc.SQLAlchemyError)
    assert e.value.message == "raising on dummy call {}".format(1)


def test_retry_with_exception_wrapping():
    # wrapping unexpected exception
    raising_exceptions = [IndexError, IndexError, ValueError]
    func = function_maker(raises=raising_exceptions)
    try_count = 6
    with pytest.raises(Exception) as e:
        # not including last exception type so it dummmy function throws in the third call.
        retry(func, exceptions=raising_exceptions[:2], wrapping_exception=DummyException, count=try_count)
    assert isinstance(e.value, DummyException)

    # wrapping failure with DummyException, instead of RetryError
    func = function_maker(raises=raising_exceptions)
    try_count = 2

    with pytest.raises(Exception) as e:
        retry(func, exceptions=raising_exceptions, wrapping_exception=DummyException, count=try_count)
    assert isinstance(e.value, DummyException)
    assert e.value.message == \
        u"Function failed {} times throwing {}".format(
            try_count,
            [(ex, "raising on dummy call {}".format(i)) for i, ex in enumerate(raising_exceptions[:try_count])])


def test_passing_retry():
    raising_exceptions = [Exception, requests.exceptions.RequestException]
    func = function_maker(raises=raising_exceptions)
    try_count = 3

    ret_value = retry(func, exceptions=raising_exceptions, count=try_count)
    assert ret_value == u"success, positional args: {}, named args: {}".format([], {})


def test_retry_with_arguments():
    raising_exceptions = [requests.exceptions.RequestException]
    func = function_maker(raises=raising_exceptions)
    try_count = 3
    _args = ["arg 1", 2]
    _kwargs = {"hi": "bye"}
    ret_value = retry(func, _args, _kwargs, exceptions=raising_exceptions, count=try_count)
    assert ret_value == u"success, positional args: {}, named args: {}".format(_args, _kwargs)


def test_retry_with_wait():
    raising_exceptions = [requests.exceptions.RequestException for _ in xrange(5)]
    func = function_maker(raises=raising_exceptions)
    try_count = 6
    _wait = 0.5
    start = time.time()
    ret_value = retry(func, wait=_wait, exceptions=raising_exceptions, count=try_count)
    assert (time.time() - start) >= (try_count-1) * _wait
    assert ret_value == u"success, positional args: {}, named args: {}".format([], {})


def test_retry_with_condition_on_retval():

    def f2_no_status():
        return ("hi")

    def f3_no_status():
        return "hi"

    def f5_no_status():
        return "hi", False, None

    def f1(status=False):
        return status

    def f2():
        return (False)

    func_without_ret_status = [f2_no_status, f3_no_status, f5_no_status]
    for fu in func_without_ret_status:
        with pytest.raises(RetryError):
            retry(fu, wait=0.2, count=2, ret_validator_func=lambda x: x[0])

    assert retry(f1, args=[True], wait=0.2, count=2, ret_validator_func=lambda x: x) is True
    assert retry(
        f1, args=[True], wait=0.2, count=2,
        ret_validator_func=lambda x: x is True) is True

    with pytest.raises(RetryError):
        retry(f2, wait=0.2, count=2, ret_validator_func=lambda x: x)

    with pytest.raises(DummyException):
        retry(f2, wait=0.2, count=2, ret_validator_func=lambda x: x, wrapping_exception=DummyException)

    assert retry(
        lambda x: x + 2,
        args=[5],
        wait=0.2,
        count=2,
        ret_validator_func=lambda x: x > 6) == 7

    with pytest.raises(RetryError):
        retry(lambda x: x + 2, args=[3], wait=0.2, count=2, ret_validator_func=lambda x: x > 6)
