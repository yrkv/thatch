
# import polars as pl

import pickle
import zlib
import json

from functools import wraps
from collections.abc import Iterable
from typing import Any


from .run import ThatchRun
from .root import ThatchRoot, MultiRunData


class MemoryRoot(ThatchRoot):
    """Storage for runs entirely in the memory of the current process.

    Instead of writing files, it maintains dicts mapping `uuid -> bytes`,
    acting as a really basic version of an in-memory filesystem. This is best
    used for small-scale isolated and quickly reproduced experiments. An empty
    instance of this is automatically created in `thatch.MEMORY_ROOT`.

    Warning: data will NOT persist past the current process unless exported
    into a different root or otherwise saved.

    TODO: shouldn't this just be replaced with a version of dir_root that
    doesn't write files? And like, in-memory sqlite db and such?
    """
    def __init__(self, ):
        self.runs = {}

    def clear(self):
        self.runs.clear()

    def save_run(self, run):
        uuid = run.info['uuid']
        run_data = run.data()
        self.runs[uuid] = zlip.compress(pickle.dumps(run_data))

    def get(self, uuids: Iterable[str]|None = None) -> MultiRunData:
        if uuids is None:
            uuids = self.runs.keys()
        assert isinstance(uuids, Iterable)

        out_runs = [
            pickle.loads(zlib.decompress(self.runs[uuid])) for uuid in uuids
        ]
        return MultiRunData(
            (run.log for uuid in uuids),
            (run.config for uuid in uuids),
            (run.info for uuid in uuids)
        )

    #def get_uuids(self, uuids: Iterable[str]|None = None) -> Iterable[str]:
    #    match uuids:
    #        case None:
    #            return list(self.configs.keys())
    #        case Iterable():
    #            return filter(lambda u: u in self.configs, uuids)
    #    assert False, "invalid input"

    #def get_runs(self, uuids: Iterable[str]|None = None) -> Iterable[list[dict]]:
    #    return (
    #        pickle.loads(zlib.decompress(self.runs[uuid]))
    #        for uuid in self.get_uuids(uuids)
    #    )

    #def get_configs(self, uuids: Iterable[str]|None = None) -> Iterable[dict[str, Any]]:
    #    return (
    #        json.loads(self.configs[uuid])
    #        for uuid in self.get_uuids(uuids)
    #    )




MEMORY_ROOT = MemoryRoot()


@wraps(ThatchRun)
def Run(**kwargs):
    return ThatchRun(root=MEMORY_ROOT, **kwargs)

