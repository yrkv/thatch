import argparse
import copy
import json
import re
import tomllib
from collections.abc import Iterator
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import yaml

from .globals import GLOBAL_CONFIG
from .util import expand_dots, flatten_dict, is_dict_str_Any


def _flat_iter_to_dict(kv_pairs: Iterator[tuple[str, Any]]):
    """Collect an iterator of key-value pairs into a flat dictionary, failing on any conflicts."""
    out = dict()
    for k, v in kv_pairs:
        if k in out:
            assert out[k] == v
        else:
            out[k] = v
    return out


def configure_from_args():
    """Gather configuration values from program arguments.

    Using `argparse`, it registers `-c` and `--config` to set configuration
    values. If provided with `<key>=<value>`, it attempts to interpret the value
    as json and set that key to that value. If provided with a file path, it
    checks for that file and tries to load it as configuration values. Each such
    arg is applied in order from left to right, with later configuration parts
    overwriting earlier parts.

    For example, let's say the original cmdline is `python train.py -c
    base_config.json -c overflow=1`, and `configure_from_args()` is called from
    somewhere within `train.py`. The file `base_config.json` is found and read
    for configuration values. Then, the configuration key "overflow" is set to
    value 1. This is applied as a context manager, just as if those same values
    had been set with a `configure()` call.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, action='append')
    args, _ = parser.parse_known_args()

    if args.config is None:
        return nullcontext()

    combined_flat_config = dict()
    for c in args.config:
        # first case is a JSON object string
        match_json = re.match(r'\{.*\}', c.strip(), re.DOTALL)
        if match_json is not None:
            j = json.loads(c)
            assert is_dict_str_Any(j)

            flat_config = _flat_iter_to_dict(flatten_dict(j))
            combined_flat_config.update(flat_config)
            continue

        # second case is {key}={value}
        match_key_eq_value = re.match('([^=]+)=([^=]+)', c.strip())
        if match_key_eq_value is not None:
            key, value = match_key_eq_value.groups()
            value = json.loads(value)
            if is_dict_str_Any(value):
                flat_config = _flat_iter_to_dict(flatten_dict({key: value}))
                combined_flat_config.update(flat_config)
            else:
                combined_flat_config[key] = value
            continue

        # third case is to read it as a file
        p = Path(c)
        assert p.exists()
        match p.suffix:
            case '.json':
                with open(p, 'rt') as f:
                    config = json.load(f)
            case '.toml':
                with open(p, 'rb') as f:
                    config = tomllib.load(f)
            case '.yaml':
                with open(p, 'rt') as f:
                    config = yaml.safe_load(f)
            case _:
                raise ValueError(f'unsupported config filetype: "{p.suffix}"')
        assert is_dict_str_Any(config)
        flat_config = _flat_iter_to_dict(flatten_dict(config))
        combined_flat_config.update(flat_config)

    expanded_config = expand_dots(combined_flat_config)
    return ConfigContextManager(expanded_config)


def configure(
    source: dict[str, Any] = {},
    **kwargs: Any,
):
    """Apply configuration values within some context.

    This applies in two ways:
        - Set default values for keyword-only parameters of functions annotated
          with `@configurable`.
        - Create/set local variables corresponding to configuration values.

    Basic usage is to set config value(s) within a context. Then, those values
    are applied to `@configurable` functions called from that context.
    > with thatch.configure(a=10, b=20):
    >     ...

    For more complex setups, it can be useful to define the configure before
    actually using it as a context manager, or chain multiple configures
    together to avoid excessive tabbing.
    > default_config = thatch.configure(lr=1e-3, steps=200)
    > extra_config = thatch.configure(lr=1e-2, foo='bar')
    > with default_config, extra_config:
    >     # config: lr=1e-2, steps=200, foo='bar'
    >     ...
    """

    expanded_source = expand_dots(source)
    expanded_kwargs = expand_dots(kwargs)
    overlap_keys = set(expanded_source.keys()) & set(expanded_kwargs.keys())
    assert len(overlap_keys) == 0
    return ConfigContextManager(expanded_source | expanded_kwargs)


class ConfigContextManager:
    """Context manager handling changes to the config, as well as reverting
    said changes upon end. By default, it targets changing/reverting
    GLOBAL_CONFIG.

    TODO: may be worthwhile to allow indexing into it, but that might have
    problems.
    """

    def __init__(self, config: dict, target: dict = GLOBAL_CONFIG):
        self.config = config
        self.target = target

    def __enter__(self):
        self.prev = copy.deepcopy(self.target)
        self.target.update(self.config)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.target.clear()
        self.target.update(self.prev)
