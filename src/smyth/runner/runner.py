import logging
import signal
import sys
import traceback
from logging.config import dictConfig
from multiprocessing import Queue
from queue import Empty
from random import randint
from time import sleep

from smyth.runner.fake_context import FakeLambdaContext
from smyth.types import LambdaHandler


def configure_logging(log_level: str):
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
                    "level": log_level,
                    "propagate": False,
                    "handlers": ["console"],
                },
            },
        }
    )


LOGGER = logging.getLogger(__name__)


def timeout_handler(signum, frame):
    raise Exception("Lambda timeout")


def lambda_invoker(
    lambda_handler: LambdaHandler,
    input_queue: Queue,
    output_queue: Queue,
    log_level: str,
):
    configure_logging(log_level=log_level)
    sys.stdin = open("/dev/stdin")

    already_faked_coldstart = False

    while True:
        try:
            message = input_queue.get(block=True, timeout=1)
        except KeyboardInterrupt:
            LOGGER.debug("Stopping process")
            sys.stdin.close()
            break
        except Empty:
            continue

        LOGGER.debug("Received message: %s", message)

        if message["type"] == "smyth.stop":
            LOGGER.debug("Stopping process")
            break

        if message.get("type") != "smyth.lambda.invoke":
            LOGGER.error("Invalid message type: %s", message.get("type"))
            continue

        event, context = message["event"], FakeLambdaContext(**message["context"])

        if (
            context.smyth["handler"]["handler_config"]["fake_coldstart"]  # type: ignore[attr-defined]
            and not already_faked_coldstart
        ):
            LOGGER.info("Faking cold start time")
            sleep(randint(500, 1000) / 1000)
            already_faked_coldstart = True

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(context.timeout))
        output_queue.put({"type": "smyth.lambda.status", "status": "working"})
        try:
            response = lambda_handler(event, context)
        except Exception as error:
            LOGGER.error("Error invoking lambda: %s", error)
            result = {
                "type": "smyth.lambda.error",
                "response": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "stacktrace": traceback.format_exc(),
                },
            }
        else:
            result = {
                "type": "smyth.lambda.response",
                "response": response,
            }
        finally:
            signal.alarm(0)
            output_queue.put({"type": "smyth.lambda.status", "status": "warm"})
        output_queue.put(result)
