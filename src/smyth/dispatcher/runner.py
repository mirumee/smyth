import json
import logging
import signal
import sys
import traceback
from logging.config import dictConfig
from multiprocessing import Queue
from queue import Empty
from multiprocessing.synchronize import Event as EventClass
from random import randint
from time import sleep, strftime, time

from aws_lambda_powertools.utilities.typing import LambdaContext

from smyth.config import HandlerConfig
from smyth.dispatcher.exceptions import LambdaTimeoutError
from smyth.schema import (
    LambdaExceptionResponse,
    LambdaHttpResponse,
    RunnerResult,
    RunnerResultType,
)
from smyth.utils import import_attribute

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "formatter": "default",
                "markup": True,
                "rich_tracebacks": True,
            },
        },
        "formatters": {
            "default": {
                "format": "[[bold red]%(processName)s[/]] %(message)s",
                "datefmt": "[%X]",
            },
        },
        "loggers": {
            "smyth": {
                "level": "NOTSET",
                "propagate": False,
                "handlers": ["console"],
            },
        },
    }
)


LOGGER = logging.getLogger(__name__)


class FakeLambdaContext(LambdaContext):
    def __init__(self, name="Fake", version="LATEST", timeout=6, **kwargs):
        self.name = name
        self.version = version
        self.created = time()
        self.timeout = timeout
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_remaining_time_in_millis(self):
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


def timeout_handler(signum, frame):
    """Raise an exception when the lambda timeout is reached.
    This will be raised from within the lambda_handler function.
    """
    raise LambdaTimeoutError("Lambda timeout")


def lambda_runner(
    name: str,
    handler_config: HandlerConfig,
    input_queue: Queue,
    output_queue: Queue,
    destruction_event: EventClass,
    is_loaded: EventClass,
    is_working: EventClass,
):
    LOGGER.setLevel(handler_config.log_level)
    sys.stdin = open("/dev/stdin")
    try:
        lambda_handler = import_attribute(handler_config.handler_path)
    except Exception as error:
        LOGGER.error("Could not import lambda handler: %s", error)
        raise

    if handler_config.fake_coldstart_time:
        LOGGER.info("Faking cold start time")
        sleep(randint(800, 1200) / 1000)

    is_loaded.set()

    while not destruction_event.is_set():
        try:
            line = input_queue.get(block=True, timeout=1)
        except Empty:
            continue
        except KeyboardInterrupt:
            LOGGER.info("Received KeyboardInterrupt, exiting")
            break
        is_working.set()
        LOGGER.debug("Received line: %s", line)
        input_data = json.loads(line)

        context = FakeLambdaContext(**input_data.get("context", {}))
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(context.timeout))

        try:
            result = lambda_handler(input_data["event"], context)
        except LambdaTimeoutError as e:
            raise
        except Exception as e:
            result = RunnerResult(
                type=RunnerResultType.EXCEPTION,
                response=LambdaExceptionResponse(
                    message=str(e),
                    type=type(e).__name__,
                    stack_trace=traceback.format_exc(),
                ),
            )
        else:
            signal.alarm(0)
            result = RunnerResult(
                type=RunnerResultType.HTTP,
                response=LambdaHttpResponse(
                    status_code=result["statusCode"],  # type: ignore[call-arg]
                    body=result.get("body", ""),
                    headers=result.get("headers", {}),
                    is_base64_encoded=result.get("isBase64Encoded", False),  # type: ignore[call-arg]
                ),
            )

        LOGGER.debug("Got result from lambda handler: %s", line)

        output_queue.put(result.model_dump_json(by_alias=True))
        is_working.clear()
    else:
        LOGGER.info("LamdaProcess '%s' exiting", name)