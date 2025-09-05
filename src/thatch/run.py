
from PIL import Image
import numpy
# import polars as pl
import psutil

#import sqlite3
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
import functools


class ThatchRun:
    def __init__(self,
                 root,
                 experiment:str = '',
                 tags:list[str] = [],
                ):

        self.root = root
        self.rows = []
        try:
            self.process = psutil.Process()
        except Exception:
            self.process = None
        # last value of each tracked key/value, even if the latest row doesn't include them.
        # key -> (step, value)
        self.merged_latest = {}
        

        self.meta_info = {}
        # the following properties are merged into `meta_info` when creating the run's entry
        self.experiment = experiment
        self.tags = tags
        self.uuid = uuid.uuid4()
        self.start_time = datetime.datetime.now()


    def __setitem__(self, key:str, value):
        assert isinstance(key, str)
        # if isinstance(value, dict):
        #     for k, v in value.items():
        #         assert isinstance(k, str)
        #         self.__setitem__(f'{key}.{k}', v)
        # else:
        self.meta_info[key] = value

    def __getitem__(self, key:str):
        assert isinstance(key, str)
        # assert len(key) > 0
        if key in self.meta_info:
            return self.meta_info[key]
        else:
            assert False, 'todo'
        # subkeys = key.split('.')
        # value = self.meta_info[key]
        # if isinstance(value, dict):
        #     for k, v in value.items():
        #         assert isinstance(k, str)
        #         self.__setitem__(f'{key}.{k}', v)
        # else:
        #     self.meta_info[key] = value


    def track_system_info(self,
                          keys=(
                          '_datetime', '_mem%', '_p_mem%', '_cpu%', '_disk%', 
                          #TODO: 'gpu%', 'gpu_temp', network usage, battery, etc.
                          ),
                          step:int=None):
        """Track a collection of built-in system information.

        Equivalent to calling `track` for each system trackable with the relevant value.
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
        self.track(kv, step=step)


    def track(self, kv:dict, step:int=None):
        # if step left unspecified, create new step when a key repeats
        if step is None:
            if self.rows == []:
                step = 0
            elif (set(kv) & set(self.rows[-1])) != set():
                step = len(self.rows)
            else:
                step = len(self.rows) - 1

        # populate rows up until step (inclusive)
        while len(self.rows) <= step:
            self.rows.append(dict())

        row = self.rows[step]
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


    def annotate_tqdm(self, bar, patterns:str|list[str]='[!_]*',
                      ignore_case=False):
        if isinstance(patterns, str):
            patterns = [patterns]

        match_function = fnmatch.fnmatch if ignore_case else fnmatch.fnmatchcase

        postfix = {}
        for key in self.merged_latest:
            include = any(match_function(key, pattern) for pattern in patterns)
            if include:
                _, postfix[key] = self.merged_latest[key]
        bar.set_postfix(postfix)

    
    def meta_entry(self):
        end_time = datetime.datetime.now()
        entry = {
            '_uuid': self.uuid.hex,
            '_experiment': self.experiment,
            # '_interval': (self.start_time, end_time),
            '_start_time': self.start_time,
            '_end_time': end_time,
            '_tags': ','.join(self.tags),
            # '_import': '', # reserve "import" column -- gets set when loaded
        }

        assert len(entry.keys() & self.meta_info.keys()) == 0
        entry.update(self.meta_info)

        return entry

    def write(self):
        self.root.save_run(self)



@functools.singledispatch
def convert(value, run:ThatchRun=None):
    print(f'warning: skipping tracking unsupported type: {type(value)}', file=sys.stderr)
    #raise TypeError(f'invalid value type for tracking: {type(value)}')

@convert.register
def _(value: Union[str, int, float, datetime.datetime], run:ThatchRun=None):
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
