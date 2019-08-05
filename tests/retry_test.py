import pytest
import time, requests, sqlalchemy
import pvHelpers as H

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
    failed = False

    with pytest.raises(H.RetryError) as exc:
        ret_value = H.retry(func, count=try_count)

    # messages are important, so not to loose trace of what has happened internal to the retry wrapper
    assert exc.value.message == \
        u"Function failed {} times throwing {}".format(try_count, \
        [(e, "raising on dummy call {}".format(i)) for i, e in enumerate(raising_exceptions[:try_count])])

def test_retry_with_unexpected_exception():
    raising_exceptions = [requests.exceptions.RequestException, sqlalchemy.exc.SQLAlchemyError]
    func = function_maker(raises=raising_exceptions)
    try_count = 3
    failed = False
    try:
        ret_value = H.retry(func, exceptions=raising_exceptions[:1], count=try_count)
    except Exception as e:
        failed = True

    assert failed
    assert isinstance(e, sqlalchemy.exc.SQLAlchemyError)
    assert e.message == "raising on dummy call {}".format(1)

def test_retry_with_exception_wrapping():
    # wrapping unexpected exception
    raising_exceptions = [IndexError, IndexError, ValueError]
    func = function_maker(raises=raising_exceptions)
    try_count = 6
    failed = False
    try:
        # not including last exception type so it dummmy function throws in the third call.
        ret_value = H.retry(func, exceptions=raising_exceptions[:2], wrapping_exception=DummyException, count=try_count)
    except Exception as e:
        failed = True

    assert failed
    assert isinstance(e, DummyException)

    # wrapping failure with DummyException, instead of RetryError
    func = function_maker(raises=raising_exceptions)
    try_count = 2
    failed = False
    try:
        ret_value = H.retry(func, exceptions=raising_exceptions, wrapping_exception=DummyException, count=try_count)
    except Exception as e:
        failed = True

    assert failed
    assert isinstance(e, DummyException)
    assert e.message == \
        u"Function failed {} times throwing {}".format(try_count, \
        [(e, "raising on dummy call {}".format(i)) for i, e in enumerate(raising_exceptions[:try_count])])

def test_passing_retry():
    raising_exceptions = [Exception, requests.exceptions.RequestException]
    func = function_maker(raises=raising_exceptions)
    try_count = 3
    failed = False
    try:
        ret_value = H.retry(func, exceptions=raising_exceptions, count=try_count)
    except Exception as e:
        failed = True

    assert not failed
    assert ret_value == u"success, positional args: {}, named args: {}".format([], {})

def test_retry_with_arguments():
    raising_exceptions = [requests.exceptions.RequestException]
    func = function_maker(raises=raising_exceptions)
    try_count = 3
    _args = ["arg 1", 2]
    _kwargs = {"hi": "bye"}
    failed = False
    try:
        ret_value = H.retry(func, _args, _kwargs, exceptions=raising_exceptions, count=try_count)
    except Exception as e:
        failed = True

    assert not failed
    assert ret_value == u"success, positional args: {}, named args: {}".format(_args, _kwargs)

def test_retry_with_wait():
    raising_exceptions = [requests.exceptions.RequestException for _ in xrange(5)]
    func = function_maker(raises=raising_exceptions)
    try_count = 6
    _wait = 0.5
    failed = False
    start = time.time()
    try:
        ret_value = H.retry(func, wait=_wait, exceptions=raising_exceptions, count=try_count)
    except Exception as e:
        failed = True

    assert (time.time() - start) >= (try_count-1)*_wait
    assert not failed
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
        with pytest.raises(H.RetryError):
            H.retry(fu, wait=0.2, count=2, ret_validator_func=lambda x: x[0])

    assert H.retry(f1, args=[True], wait=0.2, count=2, ret_validator_func=lambda x: x) is True
    assert H.retry(
        f1, args=[True], wait=0.2, count=2,
        ret_validator_func=lambda x: x is True) is True

    with pytest.raises(H.RetryError):
        H.retry(f2, wait=0.2, count=2, ret_validator_func=lambda x: x)

    with pytest.raises(DummyException):
        H.retry(f2, wait=0.2, count=2, ret_validator_func=lambda x: x, wrapping_exception=DummyException)

    assert H.retry(
        lambda x: x + 2,
        args=[5],
        wait=0.2,
        count=2,
        ret_validator_func=lambda x: x > 6) == 7

    with pytest.raises(H.RetryError):
        H.retry(lambda x: x + 2, args=[3], wait=0.2, count=2, ret_validator_func=lambda x: x > 6)
