import logging
import logging.config
from collections.abc import Iterator
from types import TracebackType
from typing import TypeVar

from starlette.requests import Request
from starlette.routing import compile_path

from smyth.context import generate_context_data
from smyth.event import generate_api_gw_v2_event_data
from smyth.exceptions import ProcessDefinitionNotFoundError
from smyth.runner.process import RunnerProcess
from smyth.runner.strategy import first_warm
from smyth.types import (
    ContextDataCallable,
    Environ,
    EventData,
    EventDataCallable,
    LambdaResponse,
    RunnerInputMessage,
    RunnerProcessProtocol,
    SmythHandler,
    StrategyGenerator,
)

Self = TypeVar("Self", bound="Smyth")

LOGGER = logging.getLogger(__name__)


class Smyth:
    smyth_handlers: dict[str, SmythHandler]
    processes: dict[str, list[RunnerProcessProtocol]]
    strategy_generators: dict[str, Iterator["RunnerProcessProtocol"]]

    def __init__(self) -> None:
        self.smyth_handlers = {}
        self.processes = {}
        self.strategy_generators = {}

    def add_handler(
        self,
        name: str,
        path: str,
        lambda_handler_path: str,
        timeout: float | None = None,
        event_data_function: EventDataCallable = generate_api_gw_v2_event_data,
        context_data_function: ContextDataCallable = generate_context_data,
        log_level: str = "INFO",
        concurrency: int = 1,
        strategy_generator: StrategyGenerator = first_warm,
        env_overrides: Environ | None = None,
    ) -> None:
        self.smyth_handlers[name] = SmythHandler(
            name=name,
            url_path=compile_path(path)[0],
            lambda_handler_path=lambda_handler_path,
            event_data_function=event_data_function,
            context_data_function=context_data_function,
            timeout=timeout,
            log_level=log_level,
            concurrency=concurrency,
            strategy_generator=strategy_generator,
            env_overrides=env_overrides,
        )

    def __enter__(self: Self) -> Self:
        self.start_runners()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: TracebackType,
    ) -> None:
        self.stop_runners()

    def start_runners(self) -> None:
        for handler_name, handler_config in self.smyth_handlers.items():
            self.processes[handler_name] = []
            for index in range(handler_config.concurrency):
                process = RunnerProcess(
                    name=f"{handler_name}:{index}",
                    lambda_handler_path=handler_config.lambda_handler_path,
                    log_level=handler_config.log_level,
                    environ_override=handler_config.get_environ(),
                )
                process.start()
                LOGGER.info("Started process %s", process.name)
                self.processes[handler_name].append(process)
            self.strategy_generators[handler_name] = handler_config.strategy_generator(
                handler_name, self.processes
            )

    def stop_runners(self) -> None:
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
        for handler_def in self.smyth_handlers.values():
            if handler_def.url_path.match(path):
                return handler_def
        raise ProcessDefinitionNotFoundError(
            f"No process definition found for path {path}"
        )

    def get_handler_for_name(self, name: str) -> SmythHandler:
        return self.smyth_handlers[name]

    async def dispatch(
        self,
        smyth_handler: SmythHandler,
        request: Request,
        event_data_function: EventDataCallable | None = None,
    ) -> LambdaResponse | None:
        """
        Smyth.dispatch is used upon a request that would normally be formed by an
        AWS trigger. It is responsible for finding the appropriate process
        for the request, invoking the process, and translating the response
        """
        try:
            process = next(self.strategy_generators[smyth_handler.name])
        except KeyError:
            raise ProcessDefinitionNotFoundError(
                f"No process definition found for handler {smyth_handler.name}"
            )

        if event_data_function is None:
            event_data_function = smyth_handler.event_data_function

        event_data = await event_data_function(request, smyth_handler, process)
        context_data = await smyth_handler.context_data_function(
            request, smyth_handler, process
        )

        return await process.asend(
            RunnerInputMessage(
                type="smyth.lambda.invoke",
                event=event_data,
                context=context_data,
            )
        )

    async def invoke(
        self, handler: SmythHandler, event_data: EventData
    ) -> LambdaResponse | None:
        """
        Smyth.invoke is used to invoke a handler directly, without going through
        Starlette or when a direct invocation is needed (e.g., when invoking
        a lambda with boto3) - on direct invocation the event holds only the data
        passed in the invokation. There's no Starlette request involved.
        """
        try:
            process = next(self.strategy_generators[handler.name])
        except KeyError:
            raise ProcessDefinitionNotFoundError(
                f"No process definition found for handler {handler.name}"
            )
        context_data = await handler.context_data_function(None, handler, process)
        return await process.asend(
            RunnerInputMessage(
                type="smyth.lambda.invoke",
                event=event_data,
                context=context_data,
            )
        )
