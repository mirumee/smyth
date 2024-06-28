import logging
from multiprocessing import Process, Queue
from queue import Empty
from time import time

from asgiref.sync import sync_to_async

from smyth.exceptions import LambdaInvocationError
from smyth.runner.runner import lambda_invoker
from smyth.types import LambdaHandler, RunnerMessage, SmythHandlerState

LOGGER = logging.getLogger(__name__)


class RunnerProcess(Process):
    name: str
    task_counter: int
    last_used_timestamp: float
    state: SmythHandlerState

    def __init__(
        self, name: str, lambda_handler: LambdaHandler, log_level: str = "INFO"
    ):
        self.name = name
        self.task_counter = 0
        self.last_used_timestamp = 0
        self.state = SmythHandlerState.COLD

        self.input_queue: Queue[RunnerMessage] = Queue(maxsize=1)
        self.output_queue: Queue[RunnerMessage] = Queue(maxsize=1)
        super().__init__(
            target=lambda_invoker,
            name=name,
            kwargs={
                "lambda_handler": lambda_handler,
                "input_queue": self.input_queue,
                "output_queue": self.output_queue,
                "log_level": log_level,
            },
        )

    def stop(self):
        self.input_queue.close()
        self.output_queue.close()
        self.input_queue.join_thread()
        self.output_queue.join_thread()
        self.terminate()
        self.join()

    def send(self, data) -> RunnerMessage | None:
        LOGGER.debug("Sending data to process %s: %s", self.name, data)
        self.task_counter += 1
        self.last_used_timestamp = time()
        self.input_queue.put(data)

        while True:
            try:
                message = self.output_queue.get(block=True, timeout=1)
            except Empty:
                continue
            except Exception as error:
                LOGGER.error("Error getting message from output queue: %s", error)
                return None

            LOGGER.debug("Received message from process %s: %s", self.name, message)
            if message["type"] == "smyth.lambda.status":
                self.state = SmythHandlerState(message["status"])
            elif message["type"] == "smyth.lambda.response":
                return message["response"]
            elif message["type"] == "smyth.lambda.error":
                LOGGER.error("Error invoking lambda: %s", message)
                raise LambdaInvocationError(message["response"]["message"])

    @sync_to_async(thread_sensitive=False)
    def asend(self, data) -> RunnerMessage | None:
        return self.send(data)
