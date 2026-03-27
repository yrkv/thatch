# import pytest
from thatch.config import configurable, configure
from thatch.config.globals import GLOBAL_CONFIG


def test_sanity():
    assert GLOBAL_CONFIG == dict()


def test_configure_without_configurable():
    c = configure(a=10, b=20)
    assert GLOBAL_CONFIG == dict()
    with c:
        assert GLOBAL_CONFIG == {'a': 10, 'b': 20}


def test_resolve_keys():
    from thatch.config.configurable import _resolve_keys

    def some_function(): ...

    assert _resolve_keys(('a', 'b', 'c'), some_function) == ('a', 'b', 'c')
    assert _resolve_keys((), some_function) == ('', 'some_function')

    class SomeClass:
        def __init__(self): ...

    class SubClass(SomeClass):
        def __init__(self): ...

    assert _resolve_keys((), SomeClass.__init__) == ('', 'SomeClass')
    # Note that subclasses do *NOT* inherit superclass config keys. Could
    # feasibly change that; would be ("", "SomeClass", "SubClass") here.
    # However, that would have a lot of other really annoying implications.
    assert _resolve_keys((), SubClass.__init__) == ('', 'SubClass')


def test_configurable_basic():
    @configurable()
    def add(*, x: int, y: int):
        return x + y

    # if there's no configure applied, an @configurable function should just be
    # equivalent to calling the underlying function
    assert add(x=3, y=4) == 7

    with configure(x=6, y=7):
        assert add() == 13
    with configure(x=6, y=7):
        assert add(y=14) == 20

    # With empty configurable keys, we can by default use the function/class
    # name as a group within the config.
    @configurable()
    def train(*, lr: float):
        return lr

    @configurable()
    def train_other(*, lr: float):
        return lr

    class SomeClass:
        @configurable()
        def __init__(self, *, lr: float, foo='bar'):
            pass

    class SubClass(SomeClass):
        @configurable()
        def __init__(self, *, lr: float, fast=True):
            # `super().__init__(...)` is just like calling any other
            # @configurable function, except any overlapping keys must have
            # matching values. (otherwise, which value goes in `self._config`?)
            #
            # If you really must call `super().__init__` with a different value,
            # you can always just `del self._config["lr"]` before invoking it.
            super().__init__(lr=lr)
            pass

    with configure(
        {
            # "default" parameter value
            'lr': 0.01,
            # Can override the base value for specific functions/classes
            'train_other.lr': 0.02,
            # Or put a whole group of overriding values
            'SomeClass': {
                'lr': 0.03,
                # ...and possibly more parameters here ofc
            },
            # `@configurable` doesn't know anything about inheritance, it only
            # knows functions -- subclasses do not inherit config values, and
            # must override superclass config values if they share them.
            'SubClass.lr': 0.04,
            # Note that without `"SubClass.lr": 0.04`, its `__init__` would
            # actually be given the base `lr=0.01`, NOT inherit the `lr=0.03`
            # from SomeClass's config.
            #
            # This may change in the future, but the added complexity of
            # enabling config inheritance would be rather messy.
        }
    ):
        assert train() == 0.01
        assert train_other() == 0.02
        trainer_object = SomeClass()
        assert trainer_object._config == {'lr': 0.03, 'foo': 'bar'}
        special_trainer = SubClass()
        assert special_trainer._config == {'lr': 0.04, 'foo': 'bar', 'fast': True}
