import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

import toml

from smyth.exceptions import ConfigFileNotFoundError


@dataclass
class HandlerConfig:
    handler_path: str
    url_path: str
    timeout: float | None = None
    event_data_function_path: str = "smyth.event.generate_api_gw_v2_event_data"
    context_data_function_path: str = "smyth.context.generate_context_data"
    log_level: str = "DEBUG"
    concurrency: int = 1
    strategy_generator_path: str = "smyth.runner.strategy.first_warm"


@dataclass
class Config:
    host: str = "0.0.0.0"
    port: int = 8080
    handlers: dict[str, HandlerConfig] = field(default_factory=dict)
    log_level: str = "INFO"
    smyth_path_prefix: str = "/smyth"

    @classmethod
    def from_dict(cls, config_dict: dict):
        handler_data = config_dict.pop("handlers")
        handlers = {
            handler_name: HandlerConfig(**handler_config)
            for handler_name, handler_config in handler_data.items()
        }
        return cls(**config_dict, handlers=handlers)


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
    if environ_config := os.environ.get("__SMYTH_CONFIG"):
        config_data = json.loads(environ_config)
        return Config.from_dict(config_data)
    return Config.from_dict(config_dict["tool"]["smyth"])


def serialize_config(config: Config) -> str:
    return json.dumps(asdict(config))
