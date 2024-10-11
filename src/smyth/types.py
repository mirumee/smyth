from collections.abc import Awaitable, Callable, Iterator, MutableMapping
from dataclasses import dataclass
from enum import Enum
from re import Pattern
from typing import Any, Protocol

from aws_lambda_powertools.utilities.typing import LambdaContext
from starlette.requests import Request

LambdaEvent = MutableMapping[str, Any]
LambdaHandler = Callable[[LambdaEvent, LambdaContext], dict[str, Any]]
RunnerMessage = MutableMapping[str, Any]
EventDataCallable = Callable[[Request], Awaitable[dict[str, Any]]]
ContextDataCallable = Callable[
    [Request | None, "SmythHandler", "RunnerProcessProtocol"], Awaitable[dict[str, Any]]
]
StrategyGenerator = Callable[
    [str, dict[str, list["RunnerProcessProtocol"]]],
    Iterator["RunnerProcessProtocol"],
]


class SmythHandlerState(str, Enum):
    COLD = "cold"
    WORKING = "working"
    WARM = "warm"


class RunnerProcessProtocol(Protocol):
    name: str
    task_counter: int
    last_used_timestamp: float
    state: SmythHandlerState

    async def asend(self, data) -> RunnerMessage | None: ...

    def stop(self): ...

    def send(self, data) -> RunnerMessage | None: ...

    def is_alive(self) -> bool: ...

    def terminate(self): ...

    def join(self): ...


@dataclass
class SmythHandler:
    name: str
    url_path: Pattern[str]
    lambda_handler_path: str
    event_data_function: EventDataCallable
    context_data_function: ContextDataCallable
    strategy_generator: StrategyGenerator
    timeout: float | None = None
    log_level: str = "INFO"
    concurrency: int = 1
