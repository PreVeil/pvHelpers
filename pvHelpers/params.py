from __future__ import absolute_import
import functools, inspect
import six
from six.moves import zip


# check if the provided types are valid Type Annotations
def __checkTAValidity(*t_as):
    for t_a in t_as:
        if isinstance(t_a, dict):
            if len(t_a) == 0:
                raise TypeError("use `{}` instead of `{}`".format(type(t_a).__name__, t_a))
            for child_t_a in t_a.values():
                __checkTAValidity(child_t_a)
        elif isinstance(t_a, (list, tuple)):
            if len(t_a) == 0:
                raise TypeError("use `{}` instead of `{}`".format(type(t_a).__name__, t_a))
            for child_t_a in t_a:
                __checkTAValidity(child_t_a)
        elif isinstance(t_a, set):
            for child_t_a in list(t_a):
                __checkTAValidity(child_t_a)

        elif not inspect.isclass(t_a):
            raise TypeError(u"`{}` is not a valid type".format(t_a))

def __checkParamValueValidity(value, type_annotation):
    if isinstance(type_annotation, dict):
        if not isinstance(value, dict):
            raise TypeError(u"provided value is not type of `{}`".format(type_annotation))
        for param_name, child_t_a in six.iteritems(type_annotation):
            if param_name not in value:
                raise KeyError(u"`{}` missing key `{}`".format(value, param_name))
            __checkParamValueValidity(value[param_name], child_t_a)
    elif isinstance(type_annotation, (tuple, list)):
        if not isinstance(value, (tuple, list)):
            raise TypeError(u"provided value is not type of `{}`".format(type(type_annotation).__name__))

        # [int], [dict] , [Class], [{"a": int}]
        if len(type_annotation) == 1:
            for element_value in value:
                __checkParamValueValidity(element_value, type_annotation[0])
        # [int, str, {"c": [int, bool, [int]]}], ...
        else:
            if len(value) != len(type_annotation):
                raise KeyError(u"provided value is not of type `{}`".format(type_annotation))
            for element_value, element_type in zip(value, type_annotation):
                __checkParamValueValidity(element_value, element_type)
    elif isinstance(type_annotation, set):
        if len(type_annotation) == 1:
            if not isinstance(value, dict):
                raise TypeError(u"provided value is not type of dict")
            for param_name, element_value in six.iteritems(value):
                if not isinstance(element_value, list(type_annotation)[0]):
                    raise TypeError(u"provided value is not of type `{}`".format(list(type_annotation)[0].__name__))
        else:
            wrong_type_count = 0
            for child_t_a in list(type_annotation):
                try:
                    __checkParamValueValidity(value, child_t_a)
                except TypeError as e:
                    wrong_type_count += 1

            if len(type_annotation) == wrong_type_count:
                raise TypeError(u"provided value is not of any of the types `{}`".format([ta.__name__ for ta in list(type_annotation)]))

    elif not isinstance(value, type_annotation):
        raise TypeError(u"provided value is not of type `{}`".format(type_annotation.__name__))

# simple decorator to check param types
# A valid type annotation is considered anything that conforms to `inspect.isclass()`
# check is done recursively on `(list, tuple, dict, set)`
# if you want dict of lists, use `()` and not `[]` => {(int)}
# dict of multiple types is considered as an OR operator: `{int, long}` => either int or long
# usage examples:
# @params(int, float, bool, {int}, {"key": PrivateKey}, [{Email}], {int, long})
def params(*types):
    __checkTAValidity(*types)
    def decoratorInstance(fn):
        func_signature, varargs, kwargs, default_values = inspect.getargspec(fn)
        if varargs or kwargs:
            raise NotImplemented(u"Don't use decorator on functions with `*`/`**` params")

        # check length of param types matching func signature
        if len(func_signature) != len(types):
            raise KeyError(u"Provided types do not match function's signature")

        # check default value types
        if default_values:
            for value, type_, param_name in zip(default_values, types[-1 * len(default_values):], func_signature[-1 * len(default_values):]):
                try:
                    __checkParamValueValidity(value, type_)
                except (TypeError, KeyError) as e:
                    raise type(e)(u"Invalid default value for arg `{}`: {}".format(param_name, e))

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Checking callers provided values
            for value, type_, param_name in zip(args, types[:len(args)], func_signature[:len(args)]):
                try:
                    __checkParamValueValidity(value, type_)
                except (KeyError, TypeError) as e:
                    raise type(e)(u"Invalid value for `{}`: {}".format(param_name, e))

            for param_name, value in six.iteritems(kwargs):
                type_ = types[func_signature.index(param_name)]
                try:
                    __checkParamValueValidity(value, type_)
                except (TypeError, KeyError) as e:
                    raise type(e)(u"Invalid value for keyword arg `{}`: {}".format(param_name, e))

            return fn(*args, **kwargs)

        return wrapper

    return decoratorInstance
