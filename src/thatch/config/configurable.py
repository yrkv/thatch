import functools
import inspect
from types import FunctionType
from typing import Any

from .globals import GLOBAL_CONFIG
from .util import index_dots


def _resolve_keys(
    keys: tuple[str, ...],
    fn: FunctionType,
) -> tuple[str, ...]:
    if keys == ():
        name = fn.__name__
        # If it's an __init__ of a class, grab the class name instead
        if name == '__init__':
            name = fn.__qualname__.split('.')[-2]
        return ('', name)
    else:
        return keys


def _update_object_config(
    obj: object,
    config: dict[str, Any],
):
    """Update the `_config` attribute of an object.

    Designed to be used when a class's `__init__` function is annotated as
    `@configurable`, to add the configured values to the `self` object directly.

    Behavior becomes very messy when both a superclass and a subclass have their
    `__init__` annotated as `@configurable`, so it is enforced that all
    overlapping configured values are equal.

    To have a subclass's config explicitly be overriden, simply pass in relevant
    args as kwargs:
        > super().__init__(lr=lr)

    Alternatively, if it gets in the way, just disable it with
    `@configurable(setattr_config_if_init=False)`
    """
    if not hasattr(obj, '_config'):
        setattr(obj, '_config', config)
    else:
        _config: dict[str, Any] = getattr(obj, '_config', config)
        overlap = _config.keys() & config.keys()
        overlap = [k for k in overlap if _config[k] != config[k]]
        overlap_dict = {k: f'{_config[k]} != {config[k]}' for k in overlap}
        assert len(overlap) == 0, f'incompatible config keys: {overlap_dict}'
        _config.update(config)


def configurable(
    *keys: str,
    reconfigure: bool = True,
    source: dict[str, Any] = GLOBAL_CONFIG,
    setattr_config_if_init: bool = True,
):
    """Function decorator to add default values to keyword-only arguments.

    The `*keys` passed into `@configurable` represent subset(s) of the source.
    These are applied in order, with the last one overriding all others.

    If `*keys` is empty, it is equivalent to `('', <name>)` instead, where
    `<name>` is the name of the function being decorated. If decorating the
    `__init__` of a class, it uses the name of that class. This way,
    function/class names can be used automatically as subgroups within the
    config either for better organization or to override more general values.

    Notes:
        - keyword-only arguments are denoted with a `*` separator in the args.
        - If you have a value that's not being properly configured, check
        for a comma after the `*`; without it, the next arg is varargs.
        - configured values override default values.
        - passed-in values override configured values.

    reconfigure:bool=True
        Re-scan the configuration source on each call, and not just the first.
        It's convenient but a bit slow, so it can be disabled if it becomes a
        bottleneck.
    source:dict=GLOBAL_CONFIG
        The dict to grab configuration data from.
    """

    config = dict()

    # Removing the ParamSpec like this prevents pyright complaining about
    # missing arguments...
    # probably better to just ignore inside tests
    # def decorator[R](fn: Callable[..., R]) -> Callable[..., R]:
    def decorator[R](fn):

        assert not isinstance(fn, type), (
            f'{fn}: @configurable should decorate __init__, not the class'
        )

        use_keys = _resolve_keys(keys, fn)

        @functools.wraps(fn)
        def decorated(*args, **kwargs) -> R:
            # @configurable does nothing with no/empty source
            if source is None or len(source) == 0:
                return fn(*args, **kwargs)

            if config == dict() or reconfigure:
                config.clear()
                for key in use_keys:
                    config.update(index_dots(source, key, default=dict()))

            sig = inspect.signature(fn)

            # just the parts of the config which are relevant to the function.
            fn_config = dict()

            for name, param in sig.parameters.items():
                if param.kind is not inspect.Parameter.KEYWORD_ONLY:
                    # If we find a non-kwonly param with a configured name, emit
                    # a warning the first time we see it.
                    if param.name in config:
                        ...  # TODO
                    continue

                # The function's configuration is defined by the keyword-only
                # params, so those are added to `fn_config`.
                if name in kwargs:
                    fn_config[name] = kwargs[name]
                elif name in config:
                    fn_config[name] = config[name]
                elif param.default is not inspect._empty:
                    fn_config[name] = param.default

            if setattr_config_if_init and fn.__name__ == '__init__':
                _update_object_config(args[0], fn_config)

            # `fn_config` only contains keyword-only args, we we need to add
            # back in the rest of the keyword args before calling it.
            new_kwargs = fn_config | kwargs
            return fn(*args, **new_kwargs)

        return decorated

    return decorator
