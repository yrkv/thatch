
import polars as pl

import pathlib
import io
import os



class ThatchRoot:
    """Defines a location for Thatch to store/write data.

    Contains a collection of experiment runs and any additional information.
    """

    # note: not required to be implemented
    def clear(self):
        raise NotImplementedError()

    def save_run(self, run):
        raise NotImplementedError()

    def get_run(self, uuid:str, meta=None):
        raise NotImplementedError()

    def get_meta(self):
        raise NotImplementedError()




