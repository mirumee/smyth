import logging
from enum import Enum
from multiprocessing import Event, Process, Queue
from multiprocessing.synchronize import Event as EventClass
from queue import Empty
from time import time

from asgiref.sync import sync_to_async

from smyth.config import HandlerConfig
from smyth.dispatcher.exceptions import DestroyedOnLoadError
from smyth.dispatcher.runner import lambda_runner
from smyth.schema import RunnerResult

LOGGER = logging.getLogger(__name__)


class ProcessState(str, Enum):
    COLD = "COLD"
    WARM = "WARM"
    WORKING = "WORKING"
    DESTROYED = "DESTROYED"


class LambdaProcess(Process):
    name: str
    task_counter: int
    last_used_timestamp: float
    handler_config: HandlerConfig
    input_queue: Queue
    output_queue: Queue
    destruction_event: EventClass
    is_loaded: EventClass

    def __init__(self, name, handler_config: HandlerConfig):
        self.name = name
        self.input_queue = Queue(maxsize=1)
        self.output_queue = Queue(maxsize=1)
        self.task_counter = 0
        self.last_used_timestamp = 0
        self.handler_config = handler_config
        self.destruction_event = Event()
        self.is_loaded = Event()
        self.is_working = Event()
        
        super().__init__(
            target=lambda_runner,
            name=name,
            kwargs={
                "name": name,
                "handler_config": handler_config,
                "input_queue": self.input_queue,
                "output_queue": self.output_queue,
                "destruction_event": self.destruction_event,
                "is_loaded": self.is_loaded,
                "is_working": self.is_working,
            },
        )

    @property
    def state(self) -> ProcessState:
        if self.is_working.is_set():
            return ProcessState.WORKING
        elif self.is_loaded.is_set():
            return ProcessState.WARM
        return ProcessState.COLD

    def run(self):
        LOGGER.info("Process %s started", self.name)
        try:
            super().run()
        except Exception:
            LOGGER.exception("Error in process %s", self.name)
            self.destruction_event.set()
            self.is_loaded.clear()
            raise

    def start(self) -> None:
        super().start()
        time_start = time()
        for _ in range(5):
            if self.destruction_event.is_set():
                raise DestroyedOnLoadError(f"Process '{self.name}' was destroyed during start.")
            if self.is_loaded.is_set():
                break
            LOGGER.debug("Waiting for process %s to load", self.name)
            self.is_loaded.wait(1)

        LOGGER.info("Process %s loaded in %s seconds", self.name, time() - time_start)

    @sync_to_async(thread_sensitive=False)
    def astart(self) -> None:
        self.start()

    def stop(self) -> None:
        self.destruction_event.set()

    def send(self, data) -> RunnerResult | None:
        LOGGER.info("Sending data to process %s: %s", self.name, data)
        self.task_counter += 1
        self.last_used_timestamp = time()
        self.input_queue.put(data)

        while not self.destruction_event.is_set():
            LOGGER.debug("SHOULD SELF DESTRUCT?: %s", self.destruction_event.is_set())
            try:
                result_data = self.output_queue.get(timeout=1)
            except Empty:
                LOGGER.debug("No data received from process %s, waiting...", self.name)
                continue
            except KeyboardInterrupt:
                self.destruction_event.set()
                return None
            if result_data:
                LOGGER.info("Received data from process %s: %s", self.name, result_data)
                return RunnerResult.model_validate_json(result_data)
        else:
            LOGGER.info("Process %s is destroyed", self.name)
            return None

    @sync_to_async(thread_sensitive=False)
    def asend(self, data) -> RunnerResult | None:
        return self.send(data)
