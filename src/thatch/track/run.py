
import copy
import uuid


from ..config.globals import GLOBAL_CONFIG



class BaseRun:

    def __init__(
        self,
        uuid,
        log:list = [],
        config:dict = {},
        experiment:str = '',
        tags:list[str] = [],
        start_time = None,
        end_time = None,
    ):
        ...


class ThatchRun(BaseRun):

    def __init__(
        self,
        experiment:str = '',
        tags:list[str] = [],
        config_source:dict = GLOBAL_CONFIG,
    ):
        log = []
        config = copy.deepcopy(config_source)
        _uuid = uuid.uuid4().hex


        ...


