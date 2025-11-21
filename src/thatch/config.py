

from collections.abc import Iterable
import functools
import inspect

from .config_util import DotDict, dot_split_index, resolve_module


"""
Global variable containing the most recently loaded configuration.
It's literally just a dict (with string keys)
"""
GLOBAL_CONFIG = dict()

# Configurable args should have a specified type, which should be one of
#  - `str`, `bool`, `int`, or `float`
#  - `list[T]` where `T` is one of the compatible types
#  - `dict[str,T]` where `T` is one of the compatible types

def configurable(*keys, reconfigure:bool=True, source:dict=GLOBAL_CONFIG):
    """
    Function decorator to add default values to keyword-only arguments.
    The `*keys` passed into `@configurable` represent subset(s) of the source.
    These are applied in order, with the last one overriding all others.
    If `*keys` is empty, it instead applies for root-level keys.

    Notes:
        - keyword-only arguments are denoted with a `*` separator in the args.
        - configured values override default values.
        - passed-in values override configured values.

    reconfigure:bool=True
        Re-scan the source on call. It's convenient but a bit slow, so it
        can be disabled if it becomes a bottleneck.
    source:dict=GLOBAL_CONFIG
        The dict to grab configuration data from.
    """

    if keys == ():
        keys = ('',)

    config = dict()
    if not reconfigure:
        for key in keys:
            config.update(dot_split_index(source, key))
    
    def decorator(fn):
        assert not isinstance(fn, type), f'{fn}: @configurable should decorate __init__, not the class'
        
        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            assert len(source) > 0, 'Empty source, did you forget to `load_configs`'
            
            if reconfigure:
                config.clear()
                for key in keys:
                    config.update(dot_split_index(source, key))
            
            sig = inspect.signature(fn)

            _config = DotDict()
            for name, param in sig.parameters.items():
                if param.kind is not inspect._KEYWORD_ONLY:
                    continue
                
                if name in kwargs:
                    _config[name] = kwargs[name]
                elif name in config:
                    _config[name] = config[name]
                elif param.default is not inspect._empty:
                    _config[name] = param.default
            
            if fn.__name__ == '__init__':
                if not hasattr(args[0], '_config'):
                    args[0]._config = _config
                else:
                    overlap = args[0]._config.keys() & _config.keys()
                    overlap = [k for k in overlap if args[0]._config[k] != _config[k]]
                    assert len(overlap) == 0, f'incompatible config keys: {overlap}'
                    args[0]._config.update(_config)

            # TODO: explain/clarify this comment -- I'm confused reading it now
            # Having `**kwargs` in the params breaks without re-adding all kwargs
            new_kwargs = _config.copy()
            new_kwargs.update(kwargs)
            return fn(*args, **new_kwargs)
        return decorated
    return decorator
