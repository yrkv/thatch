
from PIL import Image
import polars as pl
import psutil

#import sqlite3
import hashlib
import datetime
import io
import uuid
import pathlib
import os
from numbers import Number


class ThatchRun:

    def __init__(self,
                 root,
                 experiment:str = '',
                 tags:list[str] = [],
                 ):
        
        # TODO: search through parents up until an extant root is found, or initialize directory

        self.root = root
        self.experiment = experiment
        self.tags = tags

        self.rows = []
        self.uuid = uuid.uuid4()
        self.start_time = datetime.datetime.now()

        # artifacts get written to memory while tracked, and written to the respective files when
        # either `write` or `close` is called.
        # TODO: give more control over that:
        #  - what if the user has a really long run and wants to save all the artifacts to disk?
        #self.artifacts = {}
        self.meta_info = {}

        try:
            self.process = psutil.Process()
        except Exception:
            self.process = None

    def __setitem__(self, key:str, value):
        """
        """
        assert isinstance(key, str)
        if isinstance(value, dict):
            for k, v in value.items():
                assert isinstance(k, str)
                self.__setitem__(f'{key}.{k}', v)
        else:
            self.meta_info[key] = value


    def track_system_info(self,
                          keys=(
                          '_datetime', '_mem%', '_p_mem%', '_cpu%', '_disk%', 
                          #TODO: 'gpu%', 'gpu_temp'
                          ),
                          step:int=None):
        """Track a collection of built-in system information.

        Equivalent to calling `track` for each system trackable with the relevant value.
        """

        #TODO: This can *definitely* be organized/written better
        # However, most "cleaner" approaches are likely to incur overhead, so will need testing
        if '_datetime' in keys:
            self.track('_datetime', datetime.datetime.now(), step)
        if '_mem%' in keys:
            svmem = psutil.virtual_memory()
            self.track('_mem%', svmem.used / svmem.total, step)
        if '_p_mem%' in keys and self.process is not None:
            self.track('_p_mem%', self.process.memory_percent(), step)
        if '_cpu%' in keys and self.process is not None:
            self.track('_cpu%', self.process.cpu_percent(), step)
        if '_disk%' in keys:
            self.track('_disk%', psutil.disk_usage('/').percent, step)


    def track(self,
              name:str,
              value,
              step:int = None,):

        # if step left unspecified, create new step when a name repeats
        if step is None:
            if (len(self.rows) == 0) or (name in self.rows[-1]):
                step = len(self.rows)
            else:
                step = len(self.rows) - 1

        # populate rows up until step
        while len(self.rows) <= step:
            self.rows.append(dict())

        row = self.rows[step]
        assert name not in row.keys()

        if isinstance(value, (str, int, float, )):
            row[name] = value
        elif isinstance(value, Image.Image):
            f = io.BytesIO()
            im = value.convert('RGB')
            im.save(f, format='JPEG', quality=60, optimize=True,)
            im_bytes = f.getvalue()
            f.close()

            row[name] = im_bytes

            #im_hash = hashlib.md5(im_bytes).hexdigest()
            #self.artifacts[f'{im_hash}.jpg'] = im_bytes
            #row[name] = f'artifact:image:{im_hash}.jpg'
        else:
            print(f'warning: track received unsupported type: {type(value)}', file=sys.stderr)
            return
        

    def df(self):
        return pl.DataFrame(self.rows)

    def meta_entry(self):
        end_time = datetime.datetime.now()
        entry = {
            '_uuid': self.uuid.hex,
            '_experiment': self.experiment,
            '_interval': (self.start_time, end_time),
            '_tags': ','.join(self.tags),
            # '_import': '', # reserve "import" column -- gets set when loaded
        }

        assert len(entry.keys() & self.meta_info.keys()) == 0
        entry.update(self.meta_info)

        return entry

    def write(self):
        self.root.save_run(self)

    # def _write(self):
    #     end_time = datetime.datetime.now()

    #     os.makedirs(self.root / 'runs', exist_ok=True)
    #     #os.makedirs(self.root / 'artifacts', exist_ok=True)
    #     os.makedirs(self.root / 'import', exist_ok=True)

    #     # write run info to file within the root
    #     df = pl.DataFrame(self.rows)
    #     df.write_ipc(self.root / 'runs' / f'{self.uuid.hex}.arrow')

    #     # write artifact bytes to respective files
    #     #for name in self.artifacts:
    #     #    path = self.root / 'artifacts' / name
    #     #    with open(path, 'wb') as f:
    #     #        f.write(self.artifacts[name])

    #     # TODO: should run metadata be with sqlite instead? probably, but that's harder
    #     #con = sqlite3.connect(self.root / f'meta.sqlite')

    #     # TODO: use locking to avoid having data get deleted...
    #     try:
    #         meta = pl.read_ipc(self.root / 'meta.arrow')
    #     except FileNotFoundError:
    #         meta = pl.DataFrame(schema={'uuid': pl.String})

    #     run_meta_entry = {
    #         'uuid': self.uuid.hex,
    #         'experiment': self.experiment,
    #         'interval': (self.start_time, end_time),
    #         'tags': '',
    #     }

    #     assert len(run_meta_entry.keys() & self.meta_info.keys()) == 0
    #     run_meta_entry.update(self.meta_info)
        
    #     meta = pl.concat(
    #         [meta, pl.DataFrame([run_meta_entry])],
    #         how='diagonal',
    #         rechunk=True, # write_ipc doesn't work properly without this!!!
    #     )

    #     meta.write_ipc(self.root / 'meta.arrow')
    #     # with rechunk=False, this would be wrong!!!
    #     # TODO: file an issue in polars?
    #     #test = pl.read_ipc(self.root / 'meta.arrow')

