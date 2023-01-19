import pprint, inspect, datetime, traceback, requests

def px56stack(msg, prefix = '    '):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    if msg:
        print "%s PX56L:===STACK===: %s" % (now, msg)
    else:
        print "%s PX56L:===STACK===:" % now

    for line in traceback.format_stack():
        print(prefix + line.strip())
    print "%s============================" % (prefix)


def px56log(obj, *msgs, **ppobjs):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    pp = pprint.PrettyPrinter(indent=2)
    fl = inspect.stack()[1][1]
    ln = inspect.currentframe().f_back.f_lineno
    fn = inspect.stack()[1][3]
    cl = '<NoClass>'
    if obj:
        cl = obj.__class__.__name__
    if len(msgs) > 0:
        msg = ' '.join(map(lambda n: str(n), msgs))
        print "%s PX56L:- %s:%s %s.%s()\nPX56L:=" % (now, fl, ln, cl, fn), msg
    else:
        print "%s PX56L:- %s:%s %s.%s()" % (now, fl, ln, cl, fn)
    for key, value in ppobjs.items():
        print "%s PX56L:=: <%s> %s:" % (now, value.__class__.__name__, key)
        pp.pprint(value)

def px56dir(obj, prefix = "PX56L: "):
    pp = pprint.PrettyPrinter(indent=2)
    for name in dir(obj):
        if name.startswith('_'):
            pass
        else:
            if callable(getattr(obj, name)):
                pass
            else:
                print prefix, name, '=', getattr(obj, name);
