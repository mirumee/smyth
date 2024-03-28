from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from re import Pattern
from typing import Any

from starlette.requests import Request

from smyth.config import HandlerConfig
from smyth.dispatcher.process import LambdaProcess
from smyth.dispatcher.strategy import BaseDispatchStrategy


@dataclass
class ProcessDefinition:
    name: str
    handler_config: HandlerConfig
    event_data_generator: Callable[[Request], Awaitable[dict[str, Any]]]
    context_data_generator: Callable[
        [Request, "ProcessDefinition", LambdaProcess], Awaitable[dict[str, Any]]
    ]
    url_path: Pattern[str]
    dispatch_strategy_class: type[BaseDispatchStrategy]
