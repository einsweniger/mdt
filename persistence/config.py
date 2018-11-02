import os
import json
from pathlib import Path
from typing import Iterable, Tuple, Any, List
from dataclasses import dataclass, asdict
from inspect import signature, Parameter

__all__ = ['Config', 'GlobalConfig', 'get_global_config']

@dataclass
class Config:
    token: str
    user_id: int
    user_name: str
    url: str = 'moodle.uni-ulm.de'
    service: str = 'moodle_mobile_app'


def get_params() -> Iterable[Parameter]:
    for p in signature(Config).parameters.values():
        yield p


def get_defaults() -> Tuple[str, Any]:
    for parameter in get_params():
        if parameter.default is Parameter.empty:
            yield (parameter.name, None)
        else:
            yield (parameter.name, parameter.default)


def _possible_locations() -> Iterable[Path]:
    try:
        yield Path(os.environ['XDG_CONFIG_HOME']) / 'mdtconfig'
    except KeyError:
        pass
    yield Path.home() / '.config' / 'mdtconfig'
    yield Path.home() / '.mdtconfig'


def _get_config_or_create() -> Tuple[Path, Config]:
    for path in _possible_locations():
        print(path)
        if path.is_file():
            data = json.loads(path.read_text())
            return path, Config(**data)
    else:
        return _create_file()


def _create_file() -> Tuple[Path, Config]:
    for path in _possible_locations():
        if path.parent.is_dir():
            print(f'could not find global config, creating {path}...')
            defaults = dict(get_defaults())
            path.write_text(json.dumps(defaults, indent=2))
            return path, Config(**defaults)
    else:
        paths = '\n  '.join([str(p) for p in _possible_locations()])
        msg = f'could not find a location for global config, tried:\n  {paths}'
        raise FileNotFoundError(msg)


class GlobalConfig:
    def __init__(self, path: Path, config: Config):
        self.path = path
        self.config = config

    def write(self):
        self.path.write_text(json.dumps(asdict(self.config)))

    def missing_values(self) -> Iterable[str]:
        for k, v in asdict(self.config).items():
            if None is v:
                yield k


def get_global_config() -> GlobalConfig:
    return GlobalConfig(*_get_config_or_create())

