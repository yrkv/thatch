
import sqlite3
from pathlib import Path
import os
import pickle
import zlib
import json
import datetime

from functools import wraps
from collections.abc import Iterable
from typing import Any


from .run import ThatchRun
from .root import ThatchRoot, MultiRunData



class DirRoot(ThatchRoot):
    """Store run data and metadata in a `.thatch/` directory.

    ```
    .thatch/
        root.sqlite
        runs/
            7ca873a1-9673-4d1d-89d2-82a8b5b52a7a/
                log.sqlite
                config.json
            ...
    ```

    (proposed) stipulations:
        - Data should be persistent.
        - Files should never be left in an unusable/invalid/partial state.
        - Multiple threads or processes can operate with the same root and
          nothing breaks -- they may be forced to wait a moment, but try to
          minimize delays ofc.

    For now, we ignore all the extra run metadata (experiment, tags, timing, etc.)

    """

    def __init__(self, path):
        self.path = path
        os.makedirs(self.path, exist_ok=True)
        self.con = sqlite3.connect(self.path / 'root.sqlite')
        cur = self.con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS root(
                id INTEGER PRIMARY KEY,
                uuid TEXT NOT NULL UNIQUE,
                experiment TEXT NOT NULL,
                tags TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL
            ) STRICT;
        ''')
        self.con.commit()


    def save_run(self, run):
        #TODO: create <root>/<uuid> folder
        #TODO: write <root>/<uuid>/log.pickle.zlib
        #TODO: write <root>/<uuid>/config.json
        #TODO: write <root>/<uuid>/info.json
        #TODO: append to <root>/root.sqlite

        uuid = run.info['uuid']

        os.makedirs(self.path / uuid, exist_ok=True)
        with open(self.path / uuid / 'log.pickle.zlib', 'wb') as f:
            f.write(zlib.compress(pickle.dumps(run.log)))
        with open(self.path / uuid / 'config.json', 'w') as f:
            json.dump(run.config, f)
        with open(self.path / uuid / 'info.json', 'w') as f:
            json.dump(run.info, f)

        cur = self.con.cursor()
        cur.execute('''
                    INSERT OR REPLACE INTO root
                        (uuid, experiment, tags, start_time, end_time)
                    VALUES
                        (?, ?, ?, ?, ?);
                    ''',
                    (
                        run.info['uuid'],
                        run.info['experiment'],
                        run.info['tags'],
                        run.info['start_time'],
                        run.info['end_time'],
                    )
        )
        self.con.commit()

    def get(self, uuids: Iterable[str]|None = None) -> MultiRunData:
        pass
        #return (
        #    pickle.loads(zlib.decompress(self.runs[uuid]))
        #    for uuid in self.get_uuids(uuids)
        #)


    #TODO: what about the other metadata stored in root.sqlite?



def find_root():
    # locate a good spot for a `.thatch/` directory
    # (A) search parent directories for `.thatch/` dir
    # (B) search parent directories for `.git/` dir
    # (C) $PWD/.thatch/
    cwd = Path().absolute()
    parents = [cwd, *cwd.parents]
    for p in parents:
        glob_thatch = next(p.glob('.thatch/'), None)
        if glob_thatch is not None:
            return glob_thatch

    for p in parents:
        glob_git = next(p.glob('.git/'), None)
        if glob_thatch is not None:
            return p / '.thatch/'

    return cwd / '.thatch/'



DOT_THATCH_ROOT = DirRoot(find_root())


@wraps(ThatchRun)
def Run(**kwargs):
    return ThatchRun(root=DOT_THATCH_ROOT, **kwargs)



