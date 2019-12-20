import base64
import types

import simplejson

from .hook_decorators import WrapExceptions
from .params import params


class EncodingException(Exception):
    def __init__(self, exception=u""):
        super(EncodingException, self).__init__(exception)


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode)
def unicode_to_ascii(s):
    return s.encode("ascii")


def unicode_to_ascii_with_replace(s):
    return s.encode("ascii", "replace")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes)
def ascii_to_unicode(s):
    return s.encode("utf-8").decode("utf-8")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode)
def utf8_encode(s):
    return s.encode("utf-8")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes)
def utf8_decode(s):
    return s.decode("utf-8")


def unicode_if_unicode_else_decode(b):
    if isinstance(b, unicode):
        return b
    else:
        return utf8_decode(b)


def encode_content_if_unicode(content):
    if isinstance(content, unicode):
        return utf8_encode(content)
    return content


@WrapExceptions(
    EncodingException,
    [ValueError, KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes, {types.NoneType, str})
def b64enc(data, altchars=None):
    enc = base64.b64encode(data, altchars=altchars)
    return ascii_to_unicode(enc)


@WrapExceptions(
    EncodingException,
    [ValueError, KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode, {types.NoneType, str})
def b64dec(data, altchars=None):
    return base64.b64decode(data, altchars=altchars)


def to_int(data):
    if not (isinstance(data, (unicode, str)) or
            isinstance(data, (int, long, float))):
        return False, None

    try:
        return True, int(data)
    except ValueError:
        return False, None


@WrapExceptions(EncodingException, [UnicodeDecodeError, UnicodeEncodeError])
def jdumps(data, ensure_ascii=False):
    return simplejson.dumps(data, ensure_ascii=ensure_ascii)


@WrapExceptions(EncodingException, [
    KeyError, TypeError, ValueError, simplejson.JSONDecodeError,
    UnicodeDecodeError, UnicodeEncodeError
])
@params(unicode)
def jloads(data):
    return simplejson.loads(data)
