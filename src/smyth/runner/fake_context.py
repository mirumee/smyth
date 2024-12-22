import os
import sys
from collections.abc import Callable
from time import strftime, time
from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext


class FakeLambdaContext(LambdaContext):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ):
        if name is None:
            name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "Fake")
        self._name = name

        if version is None:
            version = os.environ.get("AWS_LAMBDA_FUNCTION_VERSION", "$LATEST")
        self._version = version

        self._created = time()

        if timeout is None:
            timeout = 6
        self._timeout = timeout

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_remaining_time_in_millis(self) -> int:  # type: ignore[override]
        return int(
            max(
                (self._timeout * 1000)
                - (int(round(time() * 1000)) - int(round(self._created * 1000))),
                0,
            )
        )

    @property
    def function_name(self) -> str:
        return self._name

    @property
    def function_version(self) -> str:
        return self._version

    @property
    def invoked_function_arn(self) -> str:
        return "arn:aws:lambda:serverless:" + self._name

    @property
    # This indeed is a string in the real context hence the ignore[override]
    def memory_limit_in_mb(self) -> str:  # type: ignore[override]
        return os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "128")

    @property
    def aws_request_id(self) -> str:
        return "1234567890"

    @property
    def log_group_name(self) -> str:
        return os.environ.get("AWS_LAMBDA_LOG_GROUP_NAME", f"/aws/lambda/{self._name}")

    @property
    def log_stream_name(self) -> str:
        return os.environ.get(
            "AWS_LAMBDA_LOG_STREAM_NAME",
            f"{strftime('%Y/%m/%d')}/[{self._version}]smyth_aws_lambda_log_stream_name",
        )

    @property
    def log(self) -> Callable[[str], int] | Any:
        return sys.stdout.write
