import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from multiprocessing import Process, Queue
from queue import Empty
from re import Pattern
from typing import Any

from starlette.requests import Request
from starlette.routing import compile_path

from smyth.config import Config
from smyth.runner import main
from smyth.schema import RunnerResult
from smyth.utils import import_attribute

LOGGER = logging.getLogger(__name__)


@dataclass
class ProcessDefinition:
    process: "LambdaProcess"
    event_data_generator: Callable[[Request], Awaitable[dict[str, Any]]]
    context_data_generator: Callable[[Request, float | None], Awaitable[dict[str, Any]]]
    timeout: float | None
    url_path: Pattern[str]


def get_process_definitions(config: Config) -> list[ProcessDefinition]:
    return [
        ProcessDefinition(
            process=LambdaProcess(
                target=main,
                name=handler_name,
                args=(handler_config,),
            ),
            event_data_generator=import_attribute(
                handler_config.event_data_generator_path
            ),
            context_data_generator=import_attribute(
                handler_config.context_data_generator_path
            ),
            timeout=handler_config.timeout,
            url_path=compile_path(handler_config.url_path)[0],
        )
        for handler_name, handler_config in config.handlers.items()
    ]


class LambdaProcess(Process):

    def __init__(self, target, name, args=None, kwargs=None):
        if not args:
            args = ()
        if not kwargs:
            kwargs = {}
        self.input_queue = Queue(maxsize=1)
        self.output_queue = Queue(maxsize=1)
        kwargs["input_queue"] = self.input_queue
        kwargs["output_queue"] = self.output_queue
        super().__init__(target=target, name=name, args=args, kwargs=kwargs)

    def run(self):
        LOGGER.info("Starting process %s", self.name)
        super().run()

    def send(self, data) -> RunnerResult | None:
        LOGGER.info("Sending data to process %s: %s", self.name, data)
        self.input_queue.put(data)
        try:
            result_data = self.output_queue.get()
            LOGGER.info("Received data from process %s: %s", self.name, result_data)
            return RunnerResult.model_validate_json(result_data)
        except Empty:
            return None
        except KeyboardInterrupt:
            pass
        return None
