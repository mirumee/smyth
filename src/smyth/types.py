from collections.abc import Awaitable, Callable, MutableMapping
from dataclasses import dataclass
from enum import Enum
from re import Pattern
from typing import Any, Protocol

from aws_lambda_powertools.utilities.typing import LambdaContext
from starlette.requests import Request

LambdaEvent = MutableMapping[str, Any]
LambdaHandler = Callable[[LambdaEvent, LambdaContext], dict[str, Any]]
RunnerMessage = MutableMapping[str, Any]
EventDataGenerator = Callable[[Request], Awaitable[dict[str, Any]]]
ContextDataGenerator = Callable[
    [Request, "SmythHandler", "RunnerProcessProtocol"], Awaitable[dict[str, Any]]
]
StrategyFunction = Callable[
    [str, dict[str, list["RunnerProcessProtocol"]]], "RunnerProcessProtocol"
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


@dataclass
class SmythHandler:
    name: str
    url_path: Pattern[str]
    lambda_handler: Callable[[LambdaEvent, LambdaContext], dict[str, Any]]
    event_data_generator: Callable[[Request], Awaitable[dict[str, Any]]]
    context_data_generator: Callable[
        [Request, "SmythHandler", RunnerProcessProtocol], Awaitable[dict[str, Any]]
    ]
    strategy_function: StrategyFunction
    timeout: float | None = None
    fake_coldstart: bool = False
    log_level: str = "INFO"
    concurrency: int = 1
