import logging

from starlette.requests import Request
from starlette.routing import compile_path

from smyth.context import generate_context_data
from smyth.event import generate_api_gw_v2_event_data
from smyth.exceptions import ProcessDefinitionNotFoundError
from smyth.runner.process import RunnerProcess
from smyth.runner.strategy import first_warm
from smyth.types import (
    ContextDataGenerator,
    EventDataGenerator,
    LambdaHandler,
    RunnerProcessProtocol,
    SmythHandler,
    StrategyFunction,
)

LOGGER = logging.getLogger(__name__)


class Smyth:
    handlers: dict[str, SmythHandler]
    processes: dict[str, list[RunnerProcessProtocol]]

    def __init__(self) -> None:
        self.handlers = {}
        self.processes = {}

    def add_handler(
        self,
        name: str,
        path: str,
        lambda_handler: LambdaHandler,
        timeout: float | None = None,
        event_data_generator: EventDataGenerator = generate_api_gw_v2_event_data,
        context_data_generator: ContextDataGenerator = generate_context_data,
        fake_coldstart: bool = False,
        log_level: str = "INFO",
        concurrency: int = 1,
        strategy_function: StrategyFunction = first_warm,
    ):
        self.handlers[name] = SmythHandler(
            name=name,
            url_path=compile_path(path)[0],
            lambda_handler=lambda_handler,
            event_data_generator=event_data_generator,
            context_data_generator=context_data_generator,
            timeout=timeout,
            fake_coldstart=fake_coldstart,
            log_level=log_level,
            concurrency=concurrency,
            strategy_function=strategy_function,
        )

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
        event_data_generator: EventDataGenerator | None = None,
    ):
        process = handler.strategy_function(handler.name, self.processes)
        if process is None:
            raise ProcessDefinitionNotFoundError(
                f"No process definition found for handler {handler.name}"
            )

        if event_data_generator is None:
            event_data_generator = handler.event_data_generator

        event_data = await event_data_generator(request)
        context_data = await handler.context_data_generator(request, handler, process)

        return await process.asend(
            {
                "type": "smyth.lambda.invoke",
                "event": event_data,
                "context": context_data,
            }
        )
