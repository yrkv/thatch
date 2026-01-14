
import copy
import functools
import argparse
import json
import re

#from .config import GLOBAL_CONFIG
from ..global_config import GLOBAL_CONFIG
from ..run import ThatchRun



def configure_from_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, action='append')
    args, _ = parser.parse_known_args()

    config = {}
    for c in args.config:
        if re.match(r'\{.*\}', c.strip(), re.DOTALL):
            j = json.loads(c)
            assert isinstance(j, dict)
            # TODO: add to the config...
            continue

        key_eq_value = re.match('([^=]+)=([^=]+)', c.strip(), )
        if key_eq_value is not None:
            key, value = key_eq_value.groups()
            value = json.loads(value)
            # TODO: add to the config...
            continue

        #TODO: otherwise try opening `c` as a file

        print(c)
    #return DictConfigManager()


def configure(
    source:dict|ThatchRun=None,
    **kwargs,
):
    """

    Basic usage is to set config value(s) within a context.
    > with thatch.configure(a=10, b=20):
    >     ...

    For more complex setups, it can be useful to define the configure before
    actually using it as a context manager, or chain multiple configures
    together to avoid excessive tabbing.
    > default_config = thatch.configure(lr=1e-3, steps=200)
    > extra_config = thatch.configure(lr=1e-2, foo='bar')
    > with default_config, extra_config:
    >     ...
    """
    match source:
        case None:
            dict_source = dict()
        case dict():
            dict_source = source
        case ThatchRun():
            dict_source = source.config
        case _:
            assert False, "invalid/unknown source for thatch.configure"

    config = dict_source | kwargs
    return DictConfigManager(config)


class DictConfigManager:
    def __init__(self, config:dict, target:dict=GLOBAL_CONFIG):
        self.config = config
        self.target = target

    def __enter__(self):
        self.prev = copy.deepcopy(self.target)
        #self.target.clear()
        self.target.update(self.config)
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.target.clear()
        self.target.update(self.prev)

        

