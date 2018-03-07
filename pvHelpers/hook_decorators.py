import traceback

class WrapExceptions(object):
    def __init__(self, wrapping_exception=None, exceptions=[Exception]):
        if wrapping_exception is None:
            raise TypeError("must provide a wrapping exception type")
        for exc in exceptions+ [wrapping_exception]:
            if not issubclass(exc, Exception):
                raise TypeError("{} is not subclass of Exception".format({exc}))
        self._we = wrapping_exception
        self._exs = tuple(exceptions)

    def __call__(self, function, *args, **kwargs):
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except self._exs as e:
                raise self._we(u"Function `{}` throwed {}: {}".format(function.__module__ + "." + function.__name__, type(e), traceback.format_exc()))

        return wrapper

class DoBefore(object):
    def __init__(self, handle, *args, **kwargs):
        if not callable(handle):
            raise TypeError("must provide a callable handler")

        self._handle = handle
        self._args = args
        self._kwargs = kwargs

    def __call__(self, function, *args, **kwargs):
        def wrapper(*args, **kwargs):
            setattr(self._handle, "__INNER_ARGUMENTS__", (args, kwargs))
            setattr(self._handle, "__INNER_FUNCTION__", function)
            self._handle(*self._args, **self._kwargs)
            return function(*self._handle.__INNER_ARGUMENTS__[0], **self._handle.__INNER_ARGUMENTS__[1])

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
            setattr(self._handle, "__INNER_ARGUMENTS__", (args, kwargs))
            setattr(self._handle, "__INNER_FUNCTION__", function)
            setattr(self._handle, "__INNER_RESULT__", ret)
            self._handle(*self._args, **self._kwargs)
            return ret

        return wrapper
