
class DirRoot(ThatchRoot):
    """Store run data and metadata in a `.thatch/` directory.

    `.thatch/` contains a `root.sqlite` file storing run info/metadata, such as
    each run's start time, uuid, and other run info. In the `.thatch/runs/`
    directory, we have a uuid-labeled directory for each run, were run data is
    stored. `log.pickle.zlib` stores the log of tracking information, and
    `config.json` contains the run's config (if present).

    Additional files such as visualizations or checkpoints go within a
    subdirectory `.thatch/runs/<uuid>/artifacts/`. TODO: how exactly?

    ```
    .thatch/ # root path for saving thatch run (meta)data
        root.sqlite
        runs/
            7ca873a1-9673-4d1d-89d2-82a8b5b52a7a/
                log.pickle.zlib
                config.json
                artifacts/
                    some_validation_vizualization.jpeg
                    checkpoints/
                        10.cpkt
                        20.cpkt
                        latest.ckpt
                        ...

            ...
    ```

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


    def write_run(self, run):
        ...

    def write_artifact(self, run_uuid, path, bytes):
        ...






















