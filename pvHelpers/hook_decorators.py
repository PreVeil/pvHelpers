class DoBefore(object):
    def __init__(self, handle, *args, **kwargs):
        if not callable(handle):
            raise TypeError("must provide a callable handler")

        self._handle = handle
        self._args = args
        self._kwargs = kwargs

    def __call__(self, function, *args, **kwargs):
        def wrapper(*args, **kwargs):
            self._handle.__INNER_ARGUMENTS__ = (args, kwargs)
            self._handle.__INNER_FUNCTION__ = function
            self._handle(*self._args, **self._kwargs)
            return function(*args, **kwargs)

        return wrapper


class DoAfter(object):
    def __init__(self, handle, *args, **kwargs):
        if not callable(handle):
            raise TypeError("must provide a callable handler")

        self._handle = handle
        self._args = args
        self._kwargs = kwargs

    def __call__(self, function, *args, **kwargs):
        def wrapper(*args, **kwargs):
            ret = function(*args, **kwargs)
            self._handle.__INNER_ARGUMENTS__ = (args, kwargs)
            self._handle.__INNER_FUNCTION__ = function
            self._handle.__INNER_RESULT__ = ret
            self._handle(*self._args, **self._kwargs)
            return ret

        return wrapper
