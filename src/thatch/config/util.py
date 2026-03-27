from collections.abc import Iterator
from typing import Any, TypeGuard

# type ConfigValue = str | int | float
# """Arbitrarily nestable dict with str keys
# Extra conditions:
#    - no empty string keys
#    - no dots in keys
# """
# type ConfigDict = dict[str, ConfigDict | ConfigValue]


def is_dict_str_Any(x: Any) -> TypeGuard[dict[str, Any]]:
    """
    return `True` for input strictly of type `dict[str, object]`.
    return `False` for anything else.
    """
    return isinstance(x, dict) and all(isinstance(k, str) for k in x)


def flatten_dict(
    d: dict[str, Any],
    sep: str = '.',
) -> Iterator[tuple[str, Any]]:
    """Flatten a dict into key-value pairs by joining keys from nested
    dictionaries."""
    assert is_dict_str_Any(d)

    for k, v in d.items():
        if is_dict_str_Any(v):
            for sub_k, sub_v in flatten_dict(v, sep=sep):
                yield (f'{k}{sep}{sub_k}', sub_v)
        else:
            yield (k, v)


def expand_dots(d: dict[str, Any]) -> dict[str, Any]:
    """Expand dot-delimited keys in a dictionary into nested dictionaries.

    Each key containing "." is split into parts and converted into a nested
    structure. Conflicts are not allowed, raising an exception.
    """
    assert is_dict_str_Any(d)

    out = dict()
    for k, v in flatten_dict(d):
        *k_parts, k_last = k.split('.')

        current = out
        for k_part in k_parts:
            if k_part not in current:
                current[k_part] = dict()
            current = current[k_part]
            assert isinstance(current, dict)

        if k_last in current:
            assert current[k_last] == v
        else:
            current[k_last] = v

    return out


def index_dots(
    d: dict[str, Any],
    keys_str: str,
    default: Any = None,
    raise_on_missing: bool = False,
) -> Any:
    """
    Index into a dict with a slightly extended/adjusted format:
        - index_dots(d, '') -> d
        - index_dots(d, 'foo') -> d['foo']
        - index_dots(d, 'foo.bar.baz') -> d['foo']['bar']['baz']

    The dict is assumed to NOT contain an empty string key or keys with dots.
    See `tests/test_config_util.py:test_index_dots` for clarification.
    """
    assert is_dict_str_Any(d)
    assert '' not in d

    if keys_str == '':
        return d

    keys = keys_str.split('.')
    for sub_key in keys:
        if not (isinstance(d, dict) and sub_key in d):
            if raise_on_missing:
                raise KeyError(f"Path '{keys_str}' failed at '{sub_key}'")
            return default
        d = d[sub_key]
    return d
