
# import polars as pl

import pickle
import zlib
from functools import wraps

from .run import ThatchRun
from .root import ThatchRoot


class MemoryRoot(ThatchRoot):
    """Thatch root which lives entirely in the memory of the current process.

    This is best used for small-scale isolated and quickly reproduced
    experiments. An instance of this is automatically created in MEMORY_ROOT.

    Warning: data will NOT persist past the current process unless exported
    into a different root or otherwise saved.
    """
    def __init__(self, ):
        self.meta = {}
        self.runs = {}

    def clear(self):
        self.meta.clear()
        self.runs.clear()

    def save_run(self, run):
        uuid = run.uuid.hex

        meta_entry = run.meta_entry()
        self.meta[uuid] = meta_entry

        self.runs[uuid] = zlib.compress(pickle.dumps(run.rows))
        # run_df = pl.DataFrame(run.rows)
        #TODO: compress it, but which mode is better?
        # self.runs[uuid] = run_df.write_ipc(None)
        # self.runs[uuid] = run_df.write_ipc(None)

    def get_run(self, uuid):
        # return pl.read_ipc(self.runs[uuid])
        return pickle.loads(zlib.decompress(self.runs[uuid]))

    # def get_meta
    # def get_meta(self):
    #     return pl.DataFrame(list(self.meta.values()))


MEMORY_ROOT = MemoryRoot()


@wraps(ThatchRun)
def Run(**kwargs):
    return ThatchRun(root=MEMORY_ROOT, **kwargs)

