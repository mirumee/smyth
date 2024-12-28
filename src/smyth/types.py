import os
import sys
from collections.abc import Awaitable, Callable, Iterator, MutableMapping
from dataclasses import dataclass
from enum import Enum
from re import Pattern
from time import strftime
from typing import Annotated, Any, Literal, Protocol, TypeAlias

from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel, Field
from starlette.requests import Request

LambdaEvent: TypeAlias = MutableMapping[str, Any]
EventData: TypeAlias = dict[str, Any]
EventDataCallable: TypeAlias = Callable[
    [Request, "SmythHandler", "RunnerProcessProtocol"], Awaitable[EventData]
]
ContextData: TypeAlias = dict[str, Any]
ContextDataCallable: TypeAlias = Callable[
    [Request | None, "SmythHandler", "RunnerProcessProtocol"], Awaitable[ContextData]
]
StrategyGenerator: TypeAlias = Callable[
    [str, dict[str, list["RunnerProcessProtocol"]]],
    Iterator["RunnerProcessProtocol"],
]
Environ: TypeAlias = dict[str, str]


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

    def start(self) -> None: ...

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
    env_overrides: Environ | None = None

    def _get_env_value(self, key: str, default: str) -> str:
        """
        Helper method to retrieve an environment variable value with the following
        precedence:
        1. `self.env_overrides` if defined.
        2. `os.environ` if the key exists.
        3. The provided default value.
        """
        if self.env_overrides and key in self.env_overrides:
            return self.env_overrides[key]
        return os.environ.get(key, default)

    def get_environ(self) -> Environ:
        envs = {
            "_HANDLER": self._get_env_value("_HANDLER", self.lambda_handler_path),
            "AWS_ACCESS_KEY_ID": self._get_env_value(
                "AWS_ACCESS_KEY_ID", "000000000000"
            ),
            "AWS_SECRET_ACCESS_KEY": self._get_env_value(
                "AWS_SECRET_ACCESS_KEY", "test"
            ),
            "AWS_SESSION_TOKEN": self._get_env_value("AWS_SESSION_TOKEN", "test"),
            "AWS_DEFAULT_REGION": self._get_env_value(
                "AWS_DEFAULT_REGION", "eu-central-1"
            ),
            "AWS_REGION": self._get_env_value("AWS_REGION", "eu-central-1"),
            "AWS_EXECUTION_ENV": self._get_env_value(
                "AWS_EXECUTION_ENV",
                f"AWS_Lambda_python{sys.version_info.major}.{sys.version_info.minor}",
            ),
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": self._get_env_value(
                "AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "128"
            ),
            "AWS_LAMBDA_FUNCTION_NAME": self._get_env_value(
                "AWS_LAMBDA_FUNCTION_NAME", self.name
            ),
            "AWS_LAMBDA_FUNCTION_VERSION": self._get_env_value(
                "AWS_LAMBDA_FUNCTION_VERSION", "$LATEST"
            ),
            "AWS_LAMBDA_INITIALIZATION_TYPE": self._get_env_value(
                "AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand"
            ),
            "AWS_LAMBDA_LOG_GROUP_NAME": self._get_env_value(
                "AWS_LAMBDA_LOG_GROUP_NAME", f"/aws/lambda/{self.name}"
            ),
            "AWS_LAMBDA_LOG_STREAM_NAME": self._get_env_value(
                "AWS_LAMBDA_LOG_STREAM_NAME",
                f"{strftime('%Y/%m/%d')}/[$LATEST]smyth_aws_lambda_log_stream_name",
            ),
            "AWS_LAMBDA_RUNTIME_API": self._get_env_value(
                "AWS_LAMBDA_RUNTIME_API", "127.0.0.1:9001"
            ),
            "AWS_XRAY_CONTEXT_MISSING": self._get_env_value(
                "AWS_XRAY_CONTEXT_MISSING", "LOG_ERROR"
            ),
            "AWS_XRAY_DAEMON_ADDRESS": self._get_env_value(
                "AWS_XRAY_DAEMON_ADDRESS", "127.0.0.1:2000"
            ),
        }

        return envs
