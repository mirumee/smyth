import sys
from collections.abc import Callable
from time import strftime, time
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext


class FakeLambdaContext(LambdaContext):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = "LATEST",
        timeout: int | None = None,
        **kwargs: Any,
    ):
        if name is None:
            name = "Fake"
        self.name = name

        if version is None:
            version = "LATEST"
        self.version = version

        self.created = time()

        if timeout is None:
            timeout = 6
        self.timeout = timeout

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_remaining_time_in_millis(self) -> int:  # type: ignore[override]
        return int(
            max(
                (self.timeout * 1000)
                - (int(round(time() * 1000)) - int(round(self.created * 1000))),
                0,
            )
        )

    @property
    def function_name(self) -> str:
        return self.name

    @property
    def function_version(self) -> str:
        return self.version

    @property
    def invoked_function_arn(self) -> str:
        return "arn:aws:lambda:serverless:" + self.name

    @property
    # This indeed is a string in the real context hence the ignore[override]
    def memory_limit_in_mb(self) -> str:  # type: ignore[override]
        return "1024"

    @property
    def aws_request_id(self) -> str:
        return "1234567890"

    @property
    def log_group_name(self) -> str:
        return "/aws/lambda/" + self.name

    @property
    def log_stream_name(self) -> str:
        return (
            strftime("%Y/%m/%d")
            + "/[$"
            + self.version
            + "]58419525dade4d17a495dceeeed44708"
        )

    @property
    def log(self) -> Callable[[str], int] | Any:
        return sys.stdout.write
