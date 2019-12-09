import types

from pvHelpers.utils import params
import pytest


class DummyClass(object):
    pass


dummy_instance = DummyClass()


def dummy_function():
    pass


def method_declarator(*test_params):
    try:
        @params(*test_params)
        def x(a, g):
            pass
    except Exception as e:
        print e
        raise


def method_caller(*values):
    @params(int, str, unicode, {bool, int}, {dict}, [int], (int, str),
            float, {"xx": [int], "zz": {DummyClass}}, [{types.FunctionType}])
    def call_me(a, b, c, d, e, f, g, h, i, j):
        print "valid inputs"

    try:
        call_me(*values)
    except Exception as e:
        print e
        raise


def test_type_annotations():
    method_declarator({"a": DummyClass, "bb": {(bool)}, "cc": {int, bool}}, [int])

    # 1 is not valid type
    pytest.raises(TypeError, method_declarator, DummyClass, 1)
    # dummy_instance is not valid type
    pytest.raises(TypeError, method_declarator, DummyClass, dummy_instance)
    # str is invalid type
    pytest.raises(TypeError, method_declarator, int, "string is invalid type annotation")
    # dummy_function is not valid type
    pytest.raises(TypeError, method_declarator, dummy_function, int)
    # use `list` rather than `[]`
    pytest.raises(TypeError, method_declarator, int, [])
    # use `dict` rather than `{}`
    pytest.raises(TypeError, method_declarator, {})
    # 1 is invalid type
    pytest.raises(TypeError, method_declarator, {int, 1})
    # "str" is invalid type
    pytest.raises(TypeError, method_declarator, ["str"])
    # 1 is invalid type
    pytest.raises(TypeError, method_declarator, {"a": float, "c": {int}, "x": [str, "bad type"]})
    # not enough param types given for number of the arguments
    pytest.raises(KeyError, method_declarator, int)
    # too many param types given for number of the arguments
    pytest.raises(KeyError, method_declarator, int, bool, str)


def test_arg_values_checking():
    dict_of_dicts = {i: {"i": i} for i in range(0, 1000)}
    dict_of_dummies = {i: dummy_instance for i in range(0, 1000)}
    dict_of_callables = {i: dummy_function for i in range(0, 1000)}
    list_of_ints = range(0, 1000)
    list_of_dict_of_callables = [dict_of_callables for _ in range(0, 1000)]
    valid_params = (1, "str", u"unicode", 4, dict_of_dicts, list_of_ints,
                    (3, "fixed size tuple"), 4.3, {"xx": list_of_ints, "zz": dict_of_dummies},
                    list_of_dict_of_callables)
    valid_params2 = (1, "str", u"unicode", True, dict_of_dicts, list_of_ints,
                     (3, "fixed size tuple"), 4.3, {"xx": list_of_ints, "zz": dict_of_dummies},
                     list_of_dict_of_callables)

    method_caller(*valid_params)
    method_caller(*valid_params2)

    # "str" isn't of type int
    pytest.raises(TypeError, method_caller, "str", *valid_params[1:])
    # u"u" isn't of type str
    pytest.raises(TypeError, method_caller, 1, u"u", *valid_params[2:])
    # "s" isn't of type unicode
    pytest.raises(TypeError, method_caller, 1, "u", "s", *valid_params[3:])
    # "str" isn't of either bool or int
    pytest.raises(TypeError, method_caller, 1, "u", u"s", "Str",  *valid_params[4:])
    # [1,2] isn't of type dict
    pytest.raises(TypeError, method_caller, 1, "u", u"s", True, [1, 2],  *valid_params[5:])
    # 1 isn't of type dict
    pytest.raises(TypeError, method_caller, 1, "u", u"s", 2, {"a": 1},  *valid_params[6:])
    # "b" isn't of type int
    pytest.raises(TypeError, method_caller, 1, "u", u"s", False, {"a": {"d": "d"}}, [1, "b"],  *valid_params[7:])
    # fixed sized tuple, length mismatch
    pytest.raises(KeyError, method_caller, 1, "u", u"s", 4, {"a": {"d": "d"}}, [1, 2], (1, 1, 3), *valid_params[8:])
    # dummy_instance is not of type str
    pytest.raises(
        TypeError, method_caller, 1, "u", u"s", True, {"a": {"d": "d"}}, [1, 2], (1, dummy_instance), *valid_params[9:])
    # 3 is not of type float
    pytest.raises(
        TypeError, method_caller, 1, "u", u"s", 1231, {"a": {"d": "d"}}, [1, 2], (1, "s"), 3, *valid_params[10:])
    # missing key "xx"
    pytest.raises(
        KeyError, method_caller, 1, "u", u"s", False,
        {"a": {"d": "d"}}, [1, 2], (1, "s"), 3.0, {"a": 1}, *valid_params[11:])
    # ["str", 1] is not of type DummyClass
    pytest.raises(
        TypeError, method_caller, 1, "u", u"s", 123, {"a": {"d": "d"}},
        [1, 2], (1, "s"), 3.0, {"xx": [], "zz": {"a": ["str", 1]}}, *valid_params[12:])
    # dummy_instance is not of type Function
    pytest.raises(
        TypeError, method_caller, 1, "u", u"s", 1232, {"a": {"d": "d"}},
        [1, 2], (1, "s"), 3.0, {"xx": list_of_ints, "zz": dict_of_dummies},
        [{"a": dummy_function, "v": dummy_instance}])
