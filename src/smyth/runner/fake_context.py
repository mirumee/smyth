import sys
from time import strftime, time

from aws_lambda_powertools.utilities.typing import LambdaContext


class FakeLambdaContext(LambdaContext):
    def __init__(
        self,
        name: str | None = None,
        version: str | None = "LATEST",
        timeout: int | None = None,
        **kwargs,
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
    def function_name(self):
        return self.name

    @property
    def function_version(self):
        return self.version

    @property
    def invoked_function_arn(self):
        return "arn:aws:lambda:serverless:" + self.name

    @property
    def memory_limit_in_mb(self):
        return "1024"

    @property
    def aws_request_id(self):
        return "1234567890"

    @property
    def log_group_name(self):
        return "/aws/lambda/" + self.name

    @property
    def log_stream_name(self):
        return (
            strftime("%Y/%m/%d")
            + "/[$"
            + self.version
            + "]58419525dade4d17a495dceeeed44708"
        )

    @property
    def log(self):
        return sys.stdout.write
