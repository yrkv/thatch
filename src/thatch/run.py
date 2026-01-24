
from PIL import Image
import numpy
# import polars as pl
import psutil
import torch

#import sqlite3
import copy
import hashlib
import datetime
import io
import uuid
import pathlib
import os
import sys
import fnmatch
# import zlib
from numbers import Number
from typing import Union
from typing import NamedTuple
import functools

#from .config.configurable import GLOBAL_CONFIG
from .global_config import GLOBAL_CONFIG


class RunData(NamedTuple):
    """In-memory representation of run data without any of the other
    utilities."""
    log: list
    config: dict
    info: dict



class ThatchRun:
    """A run is just a collection of data structures designed for tracking
    information about a single machine learning training run context.
    
    Each run primarily consists of the following components:
    - `log`: `list[dict[str, Any]]`
        - Step-level tracking information.
        - TODO: maybe change to a `dict[(int, str), Any]`? or some equivalent idk
    - `config`: dict[str, Any]
        - Run-level user-configurable settings.
        - Copied from thatch config on run creation, or can be set with
          `record_config` if configuration is set after the fact.
    - `info`: dict[str, Any]
        - Run-level metadata.
    """

    def __init__(self,
                 root,
                 experiment:str = '',
                 tags:list[str] = [],
                 config=GLOBAL_CONFIG,
                ):

        self.root = root
        try:
            self.process = psutil.Process()
        except Exception:
            self.process = None

        # Last value of each tracked key/value, even if the latest row doesn't
        # include them. Used for updating tqdm bar postfix.
        # key -> (step, value)
        self.merged_latest = {}

        self.log = []
        self.config = copy.deepcopy(config)
        self.info = {
            'experiment': experiment,
            'tags': tags,
            'uuid': uuid.uuid4().hex,
            'start_time': datetime.datetime.now(),
            # NOTE: end_time is updated each track
            'end_time': datetime.datetime.now(),
        }


    def record_config(self, config=GLOBAL_CONFIG):
        """Copy the current thatch config into the run.

        Optionally, a different config source can be passed in if you do not
        wish to use thatch's config system but still want to record the config.
        """
        self.config = copy.deepcopy(config)


    def track_system_info(self,
                          keys=(
                          '_datetime', '_mem%', '_p_mem%', '_cpu%', '_disk%', 
                          #TODO: gpu%, gpu_temp, network usage, battery, etc.
                          ),
                          **kwargs):
                          #step:int=None):
        """Track a collection of built-in system information.

        Equivalent to calling `track` for each system trackable in `keys` with
        the relevant value.
        """

        kv = {}
        if '_datetime' in keys:
            kv['_datetime'] = datetime.datetime.now()
        if '_mem%' in keys:
            svmem = psutil.virtual_memory()
            kv['_mem%'] = svmem.used / svmem.total
        if '_p_mem%' in keys and self.process is not None:
            kv['_p_mem%'] = self.process.memory_percent()
        if '_cpu%' in keys and self.process is not None:
            kv['_cpu%'] = self.process.cpu_percent()
        if '_disk%' in keys:
            kv['_disk%'] = psutil.disk_usage('/').percent
        self.track(kv, **kwargs)

    def track_torch_module_gradients(self,
                                     module:torch.nn.Module,
                                     prefix:str='_grad:',
                                     **kwargs):
        """Track gradient norm of each (named) parameter of a torch module.

        Prepends a prefix which defaults to '_grad:' for clarity. This can be
        removed with prefix='' or otherwise customized. If tracking multiple
        modules, consider organizing the modules in a `torch.nn.ModuleDict` to
        give each a name.
        ```
        run.track_torch_module_gradients(torch.nn.ModuleDict({
            'G': generator, 'D': discriminator
        })
        ```
        """
        kv = {}
        for name, param in module.named_parameters():
            if param.grad is None:
                kv[prefix+name] = None
                continue

            kv[prefix+name] = torch.nn.utils.get_total_norm(param.grad).item()
        self.track(kv, **kwargs)


    def track(self, kv:dict, step:int=None):
        self.info['end_time'] = datetime.datetime.now()

        # if step left unspecified, create new step when a key repeats
        if step is None:
            if self.log == []:
                step = 0
            elif (set(kv) & set(self.log[-1])) != set():
                step = len(self.log)
            else:
                step = len(self.log) - 1

        # populate log up until step (inclusive)
        while len(self.log) <= step:
            # This really shouldn't happen. Empty log means the user made a
            # mistake in 99% of cases. Maybe emit warning?
            self.log.append(dict())

        row = self.log[step]
        overlap_keys = set(kv) & set(row)
        assert overlap_keys == set(), f'overlapping keys: {overlap_keys}'

        for key, value in kv.items():
            out = convert(value)
            if out is None:
                continue
            row[key] = out
            old_step, _ = self.merged_latest.get(key, (-1, None))
            if step > old_step:
                self.merged_latest[key] = step, out


    def annotate_tqdm(self, bar, patterns:str|list[str]='[!_.]*',
                      ignore_case=False):
        """Wrapper around `tqdm.set_postfix` that automatically grabs the
        latest tracking information for keys which match an `fnmatch` pattern.
        """
        if isinstance(patterns, str):
            patterns = [patterns]

        match_function = fnmatch.fnmatch if ignore_case else fnmatch.fnmatchcase

        postfix = {}
        for key in self.merged_latest:
            include = any(match_function(key, pattern) for pattern in patterns)
            if include:
                _, postfix[key] = self.merged_latest[key]
        bar.set_postfix(postfix)


    def data(self):
        return RunData(self.log, self.config, self.info)


    def write(self, root=None):
        if root is None:
            self.root.save_run(self)
        else:
            root.save_run(self)




@functools.singledispatch
def convert(value, run:ThatchRun=None):
    print(f'warning: skipping tracking unsupported type: {type(value)}', file=sys.stderr)
    #raise TypeError(f'invalid value type for tracking: {type(value)}')

@convert.register
def _(value: Union[None, str, int, float, datetime.datetime], run:ThatchRun=None):
    return value

@convert.register
def _(value: numpy.ndarray, run:ThatchRun=None):
    f = io.BytesIO()
    numpy.save(f, value)
    out = f.getvalue()
    f.close()
    return out

@convert.register
def _(value: Image.Image, run:ThatchRun=None):
    assert False, 'todo'
