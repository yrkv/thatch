
class ThatchRoot:
    """Abstract base class representing a location for Thatch to store run data.

    In other words, it's just a collection of runs.
    """

    #def save_run(self, run: ThatchRun):
        #...

    #def get(self, uuids: Iterable[str]|None = None) -> MultiRunData:
        #...

    #def filter(self, *args, **kwargs) -> "ThatchRoot":
    def filter(self, *predicates) -> "ThatchRoot":
        """


        ```
        sub_root = root.filter(
            lambda run: 'fail' not in run.tags,
            # essentially just shorthand for
            # lambda run: 'dropout' in run.config and run.config['dropout'] > 0.4,
            Param('dropout') > 0.4,
        )
        ```

        Note: previously included **constraints in args as shorthand for equality.
        Eliminating for consistency and due to lack of flexibility of that method.
        """
        ...

    def group_by(
        self,
        key: (
            # note: `str` key(s) refer to config params; use lambda run mode to
            # group by other run info
            str
            | tuple[str, ...]
            | Callable[['ThatchRun'], Any]
            #| Callable[[dict], Any]
        ),
    ) -> list[tuple[Any, "ThatchRoot"]]:
        """
        """
        ...

    #def aggregate(self, key, aggr:str) -> 

