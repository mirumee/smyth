import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import toml

from smyth.exceptions import ConfigFileNotFoundError


@dataclass
class HandlerConfig:
    handler_path: str
    url_path: str
    timeout: float | None = None
    event_data_generator_path: str = "smyth.event.generate_event_data"
    context_data_generator_path: str = "smyth.context.generate_context_data"
    fake_coldstart_time: bool = False
    log_level: str = "INFO"
    concurrency: int = 1
    dispatch_strategy_path: str = "smyth.dispatcher.strategy.RoundRobinDispatchStrategy"


@dataclass
class Config:
    host: str = "0.0.0.0"
    port: int = 8080
    handlers: dict[str, HandlerConfig] = field(default_factory=dict)
    log_level: str = "INFO"
    smyth_path_prefix: str = "/smyth"

    def __post_init__(self):
        self.handlers = {
            handler_name: HandlerConfig(**handler_config)
            for handler_name, handler_config in self.handlers.items()
        }


def get_config_file_path(file_name: str = "pyproject.toml") -> Path:
    """Get config file path. If not found raise exception."""
    directory = Path.cwd()
    while not directory.joinpath(file_name).exists():
        if directory == directory.parent:
            raise ConfigFileNotFoundError(f"Config file {file_name} not found.")
        directory = directory.parent
    return directory.joinpath(file_name).resolve()


def get_config_dict(config_file_name: str | None = None) -> dict:
    """Get config dict."""
    if config_file_name:
        config_file_path = get_config_file_path(config_file_name)
    else:
        config_file_path = get_config_file_path()

    return toml.load(config_file_path)


def get_config(config_dict: dict) -> Config:
    """Get config."""
    return Config(**config_dict["tool"]["smyth"])


def serialize_config(config: "Config") -> str:
    """Serialize config."""
    return json.dumps(asdict(config))


def deserialize_config(config_str: str) -> Config:
    """Deserialize config."""
    return Config(**json.loads(config_str))
