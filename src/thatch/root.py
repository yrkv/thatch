
from collections import namedtuple
from functools import wraps

from collections.abc import Callable, Hashable, Iterable
from typing import Any, NamedTuple

from .run import ThatchRun


class MultiRunData(NamedTuple):
    logs: Iterable[list]
    configs: Iterable[dict]
    infos: Iterable[dict]


class ThatchRoot:
    """Abstract base class representing a location for Thatch to store run data.
    """

    def save_run(self, run: ThatchRun):
        raise NotImplementedError()

    def get(self, uuids: Iterable[str]|None = None) -> MultiRunData:
        raise NotImplementedError()

    def filter(self, *args, **kwargs) -> "ThatchRoot":
        return FilterSubRoot(self, *args, **kwargs)

    def aggregate(self, key:str, aggr:str) -> list[float | tuple | list[float]]:
        """
        Combine a key's values across all the runs in this root.

        TODO:
            - handle/consider inconsistent run shapes
            - varying step/row counts
            - missing keys in rows
                - Proposed solution -- define a `default_for_missing=None`. If
                  it's `None`, missing values are skipped during aggregation
                  (or `None` if empty). Otherwise, that's used
                  as a default.
        - implement aggregations
            - float: median, mode, min, max
            - tuple: quantiles, 95% confidence interval
            - list[float]: list
        """

        first_run = next(iter(self.get_runs()))

        run_count = 0
        out = [0.0] * len(first_run)
        for run in self.get_runs():
            #if len(run) > len(out):
                #out.extend([0.0] * )
            for i, e in enumerate(run):
                out[i] += e[key]
            run_count += 1

        for i in range(len(out)):
            out[i] /= run_count

        return out

    def group_by(
        self,
        key: (
            str
            | tuple[str, ...]
            | Callable[[dict], Any]
        ),
    ) -> list[tuple[Any, "ThatchRoot"]]:

        out = []
        for uuid in self.get_uuids():
            config, = self.get_configs([uuid])

            def map_to_value(config, key=key):
                match key:
                    case str():
                        return GroupKey(**{
                            key: config.get(key)
                        })
                    case tuple():
                        return GroupKey(**{
                            k: config.get(k) for k in key
                        })
                    case Callable():
                        # recommended to return a NamedTuple or GroupKey
                        return key(config)
                assert False, "invalid input"

            out_key = map_to_value(config)
            if out_key in (a for a,_ in out):
                continue

            def predicate(config, key=key, out_key=out_key):
                return map_to_value(config, key=key) == out_key

            out_val = self.filter(predicate)
            out.append((out_key, out_val))

        return out


class GroupKey:
    def __init__(self, **kwargs):
        # TODO: should I allow *args too? leaving the code for it commented for now
        #object.__setattr__(self, '_args', args)
        for name, value in kwargs.items():
            object.__setattr__(self, name, value)

    def __getitem__(self, key:str, /):
        return self.__dict__[key]

    def __setattr__(self, *_):
        raise AttributeError("immutable")

    def __repr__(self):
        inner = (f'{k}={repr(v)}' for k,v in self.__dict__.items())
        #inner = [
            #*(repr(v) for v in self._args),
            #*(f'{k}={repr(v)}' for k,v in self.__dict__.items() if k != '_args')
        #]
        return f'GroupKey({", ".join(inner)})'

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


    def auto_label(self) -> str:
        """
        Simple way to have 
        """
        pass



class FilterSubRoot(ThatchRoot):
    def __init__(
        self,
        parent:ThatchRoot,
        *predicates: Callable[[dict], bool],
        **constraints: (
            Callable[[Any], bool],
            Any,
        ),
    ):
        #TODO: also allow filter by info, like if it has a certain tag.
        #TODO: implement a nice way to query for nested config params,
        #   thatch.Param("train.conv_block.dropout") > 0.4
        # or (looks worse but is unambiguous)
        #   thatch.Param("train","conv_block","dropout") > 0.4
        # or (looks good but is just plain weird)
        #   thatch.Param["train"]["conv_block"]["dropout"] > 0.4
        self.parent = parent
        self.predicates = []
        for p in predicates:
            self.predicates.append(p)
        for k, v in constraints.items():
            match v:
                # note: we do the k=k,v=v stuff because python lambdas and scopes
                # are a bit weird; without it, only the final constraint applies.
                case Callable():
                    self.predicates.append(lambda c,k=k,v=v: (v(c.get(k))))
                case None:
                    self.predicates.append(lambda c,k=k: c.get(k) is None)
                case _:
                    self.predicates.append(lambda c,k=k,v=v: c.get(k) == v)

    def get_uuids(self, uuids: Iterable[str]|None = None) -> Iterable[str]:
        out = []
        for uuid in self.parent.get_uuids(uuids):
            config, = self.parent.get_configs([uuid])
            if all(p(config) for p in self.predicates):
                out.append(uuid)
        return out

    def get_runs(self, uuids: str|Iterable[str]|None = None):
        return self.parent.get_runs(self.get_uuids(uuids))
    
    def get_configs(self, uuids: str|Iterable[str]|None = None):
        return self.parent.get_configs(self.get_uuids(uuids))





