from collections.abc import Awaitable, Callable, Iterator, MutableMapping
from dataclasses import dataclass
from enum import Enum
from re import Pattern
from typing import Annotated, Any, Literal, Protocol, TypeAlias

from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel, Field
from starlette.requests import Request

LambdaEvent: TypeAlias = MutableMapping[str, Any]
EventData: TypeAlias = dict[str, Any]
EventDataCallable: TypeAlias = Callable[[Request], Awaitable[EventData]]
ContextData: TypeAlias = dict[str, Any]
ContextDataCallable: TypeAlias = Callable[
    [Request | None, "SmythHandler", "RunnerProcessProtocol"], Awaitable[ContextData]
]
StrategyGenerator: TypeAlias = Callable[
    [str, dict[str, list["RunnerProcessProtocol"]]],
    Iterator["RunnerProcessProtocol"],
]


class SmythHandlerState(str, Enum):
    COLD = "cold"
    WORKING = "working"
    WARM = "warm"


class RunnerInputMessage(BaseModel):
    type: str
    event: EventData | None = None
    context: ContextData | None = None


class LambdaResponse(BaseModel):
    status_code: int = Field(200, alias="statusCode")
    headers: dict[str, str] = {}
    body: str


class LambdaErrorResponse(BaseModel):
    type: str
    message: str
    stacktrace: str


class RunnerStatusMessage(BaseModel):
    type: Literal["smyth.lambda.status"]
    status: SmythHandlerState


class RunnerResponseMessage(BaseModel):
    type: Literal["smyth.lambda.response"]
    response: LambdaResponse


class RunnerErrorMessage(BaseModel):
    type: Literal["smyth.lambda.error"]
    error: LambdaErrorResponse


RunnerOutputMessage = Annotated[
    RunnerStatusMessage | RunnerResponseMessage | RunnerErrorMessage,
    Field(discriminator="type"),
]


LambdaHandler: TypeAlias = Callable[[LambdaEvent, LambdaContext], LambdaResponse]


class RunnerProcessProtocol(Protocol):
    name: str
    task_counter: int
    last_used_timestamp: float
    state: SmythHandlerState

    async def asend(self, data: RunnerInputMessage) -> LambdaResponse | None: ...

    def stop(self) -> None: ...

    def send(self, data: RunnerInputMessage) -> LambdaResponse | None: ...

    def is_alive(self) -> bool: ...

    def terminate(self) -> None: ...

    def join(self) -> None: ...


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
