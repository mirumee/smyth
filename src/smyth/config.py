from dataclasses import dataclass, field
from pathlib import Path

import toml

from smyth.exceptions import ConfigFileNotFoundError


@dataclass
class HandlerConfig:
    handler_path: str
    url_path: str
    timeout: float | None = None
    event_data_generator_path: str = "smyth.event.generate_api_gw_v2_event_data"
    context_data_generator_path: str = "smyth.context.generate_context_data"
    fake_coldstart: bool = False
    log_level: str = "INFO"
    concurrency: int = 1
    strategy_function_path: str = "smyth.runner.strategy.first_warm"


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
