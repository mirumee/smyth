import inspect
import logging
import logging.config
import signal
import sys
import traceback
from collections.abc import Generator
from multiprocessing import Process, Queue, set_start_method
from queue import Empty
from time import time
from types import FrameType

from asgiref.sync import sync_to_async
from setproctitle import setproctitle

from smyth.exceptions import (
    LambdaHandlerLoadError,
    LambdaInvocationError,
    LambdaTimeoutError,
    SubprocessError,
)
from smyth.runner.fake_context import FakeLambdaContext
from smyth.types import (
    EventData,
    LambdaHandler,
    LambdaResponse,
    RunnerInputMessage,
    RunnerOutputMessage,
    SmythHandlerState,
)
from smyth.utils import get_logging_config, import_attribute

set_start_method("spawn", force=True)
LOGGER = logging.getLogger(__name__)


class RunnerProcess(Process):
    name: str
    task_counter: int
    last_used_timestamp: float
    state: SmythHandlerState

    def __init__(self, name: str, lambda_handler_path: str, log_level: str = "INFO"):
        self.name = name
        self.task_counter = 0
        self.last_used_timestamp = 0
        self.state = SmythHandlerState.COLD

        self.input_queue: Queue[RunnerInputMessage] = Queue(maxsize=1)
        self.output_queue: Queue[RunnerOutputMessage] = Queue(maxsize=1)

        self.lambda_handler_path = lambda_handler_path
        self.log_level = log_level
        super().__init__(
            name=name,
        )

    def stop(self) -> None:
        self.input_queue.put({"type": "smyth.stop"})
        self.join()
        self.input_queue.close()
        self.output_queue.close()
        self.input_queue.join_thread()
        self.output_queue.join_thread()

    def send(self, data: RunnerInputMessage) -> LambdaResponse | None:
        LOGGER.debug("Sending data to process %s: %s", self.name, data)
        self.task_counter += 1
        self.last_used_timestamp = time()
        self.input_queue.put(data)

        while True:
            if not self.is_alive():
                LOGGER.error(
                    "Process is not alive, this should generally not happen. "
                    "Restart Smyth and check your configuration. "
                    "This often happens when the handler can't be loaded "
                    "(i.e. an exception is raised when importing the handler)."
                )
                raise SubprocessError("Process is not alive")
            try:
                message = self.output_queue.get(block=True, timeout=1)
            except Empty:
                continue
            except Exception as error:
                LOGGER.error("Error getting message from output queue: %s", error)
                return None

            LOGGER.debug("Received message from process %s: %s", self.name, message)
            if message["type"] == "smyth.lambda.status":
                if not (status := message.get("status")):
                    LOGGER.error("No status provided")
                    continue
                self.state = SmythHandlerState(status)
            elif message["type"] == "smyth.lambda.response":
                self.state = SmythHandlerState.WARM
                if not (response := message.get("response")):
                    LOGGER.error("No response provided")
                    continue
                return response
            elif message["type"] == "smyth.lambda.error":
                self.state = SmythHandlerState.WARM
                if not (error_data := message.get("error")):
                    LOGGER.error("No error provided")
                    continue
                if error_data["type"] == "LambdaTimeoutError":
                    raise LambdaTimeoutError(error_data["message"])
                else:
                    raise LambdaInvocationError(error_data["message"])

    @sync_to_async(thread_sensitive=False)
    def asend(self, data: RunnerInputMessage) -> LambdaResponse | None:
        return self.send(data)

    # Backend

    def run(self) -> None:
        setproctitle(f"smyth:{self.name}")
        logging.config.dictConfig(get_logging_config(self.log_level))
        self.lambda_invoker__()

    def get_message__(self) -> Generator[RunnerInputMessage, None, None]:
        while True:
            try:
                message = self.input_queue.get(block=True, timeout=1)
            except KeyboardInterrupt:
                LOGGER.debug("Stopping process")
                return
            except Empty:
                continue
            else:
                LOGGER.debug("Received message: %s", message)
                if message["type"] == "smyth.stop":
                    LOGGER.debug("Stopping process")
                    return
                yield message

    def get_event__(self, message: RunnerInputMessage) -> EventData:
        if (event := message.get("event")) is None:
            raise LambdaInvocationError("No event data provided")
        return event

    def get_context__(self, message: RunnerInputMessage) -> FakeLambdaContext:
        if (context := message.get("context")) is None:
            raise LambdaInvocationError("No context data provided")
        return FakeLambdaContext(**context)

    def import_handler__(
        self, lambda_handler_path: str, event: EventData, context: FakeLambdaContext
    ) -> LambdaHandler:
        LOGGER.info("Starting cold, importing '%s'", lambda_handler_path)
        try:
            handler: LambdaHandler = import_attribute(lambda_handler_path)
        except ImportError as error:
            raise LambdaHandlerLoadError(
                f"Error importing handler: {error}, module not found"
            ) from error
        except AttributeError as error:
            raise LambdaHandlerLoadError(
                f"Error importing handler: {error}, attribute in module not found"
            ) from error

        sig = inspect.signature(handler)
        try:
            sig.bind(event, context)
        except TypeError:
            LOGGER.warning(
                "Handler signature does not match event and context, "
                "using `event` and `context` as parameters."
            )
        return handler

    def set_status__(self, status: SmythHandlerState) -> None:
        self.output_queue.put({"type": "smyth.lambda.status", "status": status})

    @staticmethod
    def timeout_handler__(signum: int, frame: FrameType | None) -> None:
        raise LambdaTimeoutError("Lambda timeout")

    def lambda_invoker__(self) -> None:
        sys.stdin = open("/dev/stdin")
        lambda_handler: LambdaHandler | None = None
        self.set_status__(SmythHandlerState.COLD)

        for message in self.get_message__():
            if message.get("type") != "smyth.lambda.invoke":
                LOGGER.error("Invalid message type: %s", message.get("type"))
                continue

            event = self.get_event__(message)
            context = self.get_context__(message)

            if not lambda_handler:
                lambda_handler = self.import_handler__(
                    self.lambda_handler_path,
                    event,
                    context,
                )
                self.set_status__(SmythHandlerState.WARM)

            signal.signal(signal.SIGALRM, self.timeout_handler__)
            signal.alarm(int(context.timeout))
            self.set_status__(SmythHandlerState.WORKING)
            try:
                response = lambda_handler(event, context)
            except Exception as error:
                LOGGER.exception(
                    "Error invoking lambda: %s",
                    error,
                    extra={"log_setting": "console_full_width"},
                )
                self.output_queue.put(
                    {
                        "type": "smyth.lambda.error",
                        "error": {
                            "type": type(error).__name__,
                            "message": str(error),
                            "stacktrace": traceback.format_exc(),
                        },
                    }
                )
            else:
                self.output_queue.put(
                    {
                        "type": "smyth.lambda.response",
                        "response": response,
                    }
                )
            finally:
                signal.alarm(0)
