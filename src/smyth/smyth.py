import logging
from collections.abc import Iterator

from starlette.requests import Request
from starlette.routing import compile_path

from smyth.context import generate_context_data
from smyth.event import generate_api_gw_v2_event_data
from smyth.exceptions import ProcessDefinitionNotFoundError
from smyth.runner.process import RunnerProcess
from smyth.runner.strategy import first_warm
from smyth.types import (
    ContextDataCallable,
    EventDataCallable,
    LambdaHandler,
    RunnerProcessProtocol,
    SmythHandler,
    StrategyGenerator,
)

LOGGER = logging.getLogger(__name__)


class Smyth:
    handlers: dict[str, SmythHandler]
    processes: dict[str, list[RunnerProcessProtocol]]
    strategy_generators: dict[str, Iterator["RunnerProcessProtocol"]]

    def __init__(self) -> None:
        self.handlers = {}
        self.processes = {}
        self.strategy_generators = {}

    def add_handler(
        self,
        name: str,
        path: str,
        lambda_handler: LambdaHandler,
        timeout: float | None = None,
        event_data_function: EventDataCallable = generate_api_gw_v2_event_data,
        context_data_function: ContextDataCallable = generate_context_data,
        fake_coldstart: bool = False,
        log_level: str = "INFO",
        concurrency: int = 1,
        strategy_generator: StrategyGenerator = first_warm,
    ):
        self.handlers[name] = SmythHandler(
            name=name,
            url_path=compile_path(path)[0],
            lambda_handler=lambda_handler,
            event_data_function=event_data_function,
            context_data_function=context_data_function,
            timeout=timeout,
            fake_coldstart=fake_coldstart,
            log_level=log_level,
            concurrency=concurrency,
            strategy_generator=strategy_generator,
        )

    def __enter__(self):
        self.start_runners()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_runners()

    def start_runners(self):
        for handler_name, handler_config in self.handlers.items():
            self.processes[handler_name] = []
            for index in range(handler_config.concurrency):
                process = RunnerProcess(
                    name=f"{handler_name}:{index}",
                    lambda_handler=handler_config.lambda_handler,
                    log_level=handler_config.log_level,
                )
                process.start()
                LOGGER.info("Started process %s", process.name)
                self.processes[handler_name].append(process)
            self.strategy_generators[handler_name] = handler_config.strategy_generator(
                handler_name, self.processes
            )

    def stop_runners(self):
        for process_group in self.processes.values():
            for process in process_group:
                LOGGER.info("Stopping process %s", process.name)
                process.stop()
        for process_group in self.processes.values():
            for process in process_group:
                LOGGER.debug("Joining process %s", process.name)
                if process.is_alive():
                    process.terminate()
                    process.join()

    def get_handler_for_request(self, path: str) -> SmythHandler:
        for handler_def in self.handlers.values():
            if handler_def.url_path.match(path):
                return handler_def
        raise ProcessDefinitionNotFoundError(
            f"No process definition found for path {path}"
        )

    def get_handler_for_name(self, name: str) -> SmythHandler:
        return self.handlers[name]

    async def dispatch(
        self,
        handler: SmythHandler,
        request: Request,
        event_data_function: EventDataCallable | None = None,
    ):
        process = next(self.strategy_generators[handler.name])
        if process is None:
            raise ProcessDefinitionNotFoundError(
                f"No process definition found for handler {handler.name}"
            )

        if event_data_function is None:
            event_data_function = handler.event_data_function

        event_data = await event_data_function(request)
        context_data = await handler.context_data_function(request, handler, process)

        return await process.asend(
            {
                "type": "smyth.lambda.invoke",
                "event": event_data,
                "context": context_data,
            }
        )

    async def invoke(self, handler: SmythHandler, event_data: dict):
        process = next(self.strategy_generators[handler.name])
        if process is None:
            raise ProcessDefinitionNotFoundError(
                f"No process definition found for handler {handler.name}"
            )
        context_data = await handler.context_data_function(None, handler, process)
        return await process.asend(
            {
                "type": "smyth.lambda.invoke",
                "event": event_data,
                "context": context_data,
            }
        )
