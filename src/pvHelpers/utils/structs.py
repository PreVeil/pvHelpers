import collections
import copy
import itertools


class CaseInsensitiveSet(collections.Set):
    def __init__(self, lyst):
        self.data = CaseInsensitiveDict()
        for e in lyst:
            self.data[e] = e

    def __contains__(self, item):
        return item in self.data

    def __iter__(self):
        for _, n in self.data.iteritems():
            yield n

    def __len__(self):
        return len(self.data)

    def union(self, other):
        if not isinstance(other, list):
            raise TypeError(u"other must be of type list")

        new = CaseInsensitiveDict(copy.deepcopy(self.data))
        for o in other:
            new[o] = o

        return CaseInsensitiveSet(new.values())

    def difference(self, other):
        if not isinstance(other, list):
            raise TypeError(u"other must be of type list")
        new = CaseInsensitiveDict(copy.deepcopy(self.data))
        for o in other:
            if o in new:
                del new[o]

        return CaseInsensitiveSet(new.values())


# Lifted from m000 @ http://stackoverflow.com/a/32888599
class CaseInsensitiveDict(dict):
    @classmethod
    def _k(cls, key):
        if isinstance(key, basestring):
            return key.lower()
        elif isinstance(key, tuple):
            return tuple([cls._k(i) for i in key])
        else:
            return key

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(self.__class__._k(key))

    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(self.__class__._k(key), value)

    def __delitem__(self, key):
        return super(CaseInsensitiveDict, self).__delitem__(self.__class__._k(key))

    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(self.__class__._k(key))

    def has_key(self, key):
        return self.__class__._k(key) in super(CaseInsensitiveDict, self)

    def pop(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)

    def update(self, e={}, **f):
        super(CaseInsensitiveDict, self).update(self.__class__(e))
        super(CaseInsensitiveDict, self).update(self.__class__(**f))

    def _convert_keys(self):
        for k in list(self.keys()):
            v = super(CaseInsensitiveDict, self).pop(k)
            self.__setitem__(k, v)


# https://docs.python.org/dev/library/itertools.html#itertools-recipes
def partition(pred, iterable):
    """ Use a predicate to partition entries into false entries and true entries """

    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = itertools.tee(iterable)
    return filter(pred, t2), filter(lambda x: not pred(x), t1)


def merge_dicts(*args):
    ret = {}
    for _dict in args:
        if not isinstance(_dict, dict):
            raise TypeError(u"merge_dicts: Arguments must be of type dict")
        ret.update(_dict)
    return ret
