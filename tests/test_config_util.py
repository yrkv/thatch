import pytest


def test_is_dict_str_Any():
    from thatch.config.util import is_dict_str_Any

    assert is_dict_str_Any({})
    assert is_dict_str_Any({'a': 10})
    assert not is_dict_str_Any({(10, 20): 'b'})
    assert not is_dict_str_Any({'a': 10, ('b',): 20})


def test_expand_dots():
    from thatch.config.util import expand_dots

    assert expand_dots({}) == {}
    assert expand_dots({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    assert expand_dots({'a.b': 1}) == {'a': {'b': 1}}
    assert expand_dots({'a.b.c': 1}) == {'a': {'b': {'c': 1}}}
    assert expand_dots({'a.b': 1, 'a.c': 2}) == {'a': {'b': 1, 'c': 2}}
    assert expand_dots({'a': {'b.c': 1}}) == {'a': {'b': {'c': 1}}}

    # test variations with empty string(s)
    assert expand_dots({'.a': 1}) == {'': {'a': 1}}
    assert expand_dots({'a.': 1}) == {'a': {'': 1}}
    assert expand_dots({'.': 1}) == {'': {'': 1}}
    assert expand_dots({'a..b': 1}) == {'a': {'': {'b': 1}}}

    # test multiple ways to reach "a.*", with both orderings
    assert expand_dots({'a.b': 1, 'a': {'c': 2}}) == {'a': {'b': 1, 'c': 2}}
    assert expand_dots({'a': {'c': 2}, 'a.b': 1}) == {'a': {'b': 1, 'c': 2}}

    # "conflicts" are fine if the values are identical
    assert expand_dots({'a.b': 1, 'a': {'b': 1}}) == {'a': {'b': 1}}

    # 'a.b' would have to be two different values here
    with pytest.raises(Exception):
        expand_dots({'a.b': 1, 'a': {'b': 2}})
    # Similarly, here 'a' would have to be both =1 and a dict
    with pytest.raises(Exception):
        expand_dots({'a': 1, 'a.b': 2})
    # And with reversed order, just in case
    with pytest.raises(Exception):
        expand_dots({'a.b': 2, 'a': 1})


type ConfigValue = str | int | float
type ConfigDict = dict[str, ConfigDict | ConfigValue]


def test_index_dots():
    from thatch.config.util import index_dots

    # is there a good way to have pyright be fine with variably nested dicts?
    # or should I just have it ignore it and not worry about it lol
    d = {
        'a': {
            'b': {'c': 10},
            'd': 20,
        },
    }

    assert index_dots(d, '') == d
    assert index_dots(d, 'a') == d['a']
    assert index_dots(d, 'a.b') == d['a']['b']
    assert index_dots(d, 'a.d') == d['a']['d']
    assert index_dots(d, 'a.b.c') == d['a']['b']['c']

    assert index_dots(d, 'x') is None
    assert index_dots(d, 'x', default=-1) == -1

    with pytest.raises(Exception):
        index_dots(d, 'x', raise_on_missing=True)
    with pytest.raises(Exception):
        index_dots(d, 'a.x', raise_on_missing=True)
    with pytest.raises(Exception):
        index_dots(d, 'a.b.c.x', raise_on_missing=True)
