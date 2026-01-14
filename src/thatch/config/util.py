import functools

import torch


class DotDict(dict):
    """
    `dict` which additionally allows using dot notation for indexing.
    This only works for getting -- use brackets to set values like normal.
    Naturally, this also only works for string keys which can be identifiers.

    ```
    dotdict = DotDict({'a': 10, 'foo': {'bar': 20}})
    dotdict.a       # -> 10
    dotdict.foo     # -> {'bar': 20}
    dotdict.foo.bar # -> 20
    ```

    Note: IPython reacts weirdly internally to DotDict when trying to `display`
          it, but this doesn't cause any known issues.
    """

    def __getattr__(self, key:str, /):
        out = self[key]
        if isinstance(out, dict):
            out = DotDict(out)
        return out

    # __getstate__ and __setstate__ are used for pickling and unpickling
    # For simplicity, we make it pickle and unpickle as a native dict
    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        self.clear()
        self.update(state)


def dot_split_index(d:dict, keys_str:str, default=None):
    """
    Index into a dict with a slightly
    extended format:
        - config_index('') -> dict
        - config_index('foo') -> dict['foo']
        - config_index('foo.bar.baz') -> dict['foo']['bar']['baz']
    """
    if keys_str == '':
        return d

    keys = keys_str.split('.')
    for sub_key in keys:
        if sub_key not in d:
            return default
            #raise KeyError(
            #    f'No key "{sub_key}" in keys {d.keys()} when resolving "{keys_str}"'
            #)
        d = d[sub_key]
    return d


def resolve_module(
    config: (
        str
        | dict[str,dict]
        | torch.nn.Module
    ),
    search_globals=False
) -> torch.nn.Module:
    if isinstance(config, torch.nn.Module):
        return config

    if isinstance(config, str):
        name, kw_args, star_args = config, {}, []
    else:
        name, = config.keys()
        kw_args = config[name].copy()
        star_args = kw_args.pop('*args', [])
    
    if hasattr(torch.nn, name):
        cls = getattr(torch.nn, name)
        return functools.partial(cls, *star_args, **kw_args)

    # still unsure about this approach, so keep it disabled by default
    if search_globals:
        g = globals()
        if name in g:
            cls = g[name]
            return functools.partial(cls, *star_args, **kw_args)

    assert False, "TODO: handle invalid input"


def pretty_config(config):
    match config:
        case dict():
            if len(config) == 1:
                name, = config.keys()
                if isinstance(config[name], dict):
                    kw_args = config[name].copy()
                    star_args = kw_args.pop('*args', [])
                    args = [
                        *(f'{pretty_config(arg)}' for arg in star_args),
                        *(f'{key}={pretty_config(val)}' for key,val in kw_args.items()),
                    ]
                    if len(args) == 0:
                        return name
                    return f'{name}({",".join(args)})'
            return str({key: pretty_config(val) for key,val in config.items()})
        case list(): # list case should only happen in recursive sub-calls
            return str([pretty_config(c) for c in config])

    return config


