import types, time, traceback

class RetryError(Exception):
    def __init__(self, message="Retry Wrapper Exception"):
        super(RetryError, self).__init__(message)

def retry(func, args=[], kwargs={}, exceptions=[Exception], count=2, wait=0, wrapping_exception=None):
    if not callable(func):
        raise RetryError(u"func must be of type callable")
    if not isinstance(args, list):
        raise RetryError(u"args must be of type list")
    if not isinstance(kwargs, dict):
        raise RetryError(u"kwargs must be of type dict")
    if not isinstance(exceptions, (list, tuple)):
        raise RetryError(u"exceptions must be of type tuple")
    for exc in exceptions:
        if not issubclass(exc, Exception):
            raise RetryError(u"exception must be of type Exception {}".format(exc))
    exceptions = tuple(exceptions) if isinstance(exceptions, list) else exceptions
    if not isinstance(count, int):
        raise RetryError(u"count must be of type int")
    if not isinstance(wait, (int, float)):
        raise RetryError(u"wait must be of type float")
    if not (wrapping_exception is None or issubclass(wrapping_exception, Exception)):
        raise RetryError(u"wrapping_exception must be of type Exception/None")

    exception_stack = []
    for it in xrange(0, count):
        try:
            # TODO: it's worth devising a way to let caller know the function succeeded after
            # how many times of try, it'd help tuning the retry count
            return_value = func(*args, **kwargs)
        except exceptions as e:
            exception_stack.append(e)
            if wait > 0:
                # should we use normal sleep vs monkey_patched?
                time.sleep(wait)
            continue
        except Exception as e:
            if wrapping_exception:
                raise wrapping_exception(u"Function `{}` throwed {}: {}".format(func.__module__ + "." + func.__name__, type(e), traceback.format_exc()))
            raise
        else:
            # TODO: we can add conditions for value of `return_value` so to perform retry upon them
            return return_value

    msg = u"Function failed {} times throwing {}".format(len(exception_stack), [(type(exc), exc.message) for exc in exception_stack])
    if wrapping_exception:
        raise wrapping_exception(msg)
    raise RetryError(msg)
