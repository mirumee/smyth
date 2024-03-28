import json
import logging

from starlette.requests import Request
from starlette.routing import compile_path

from smyth.config import Config
from smyth.dispatcher.exceptions import (
    NoAvailableProcessError,
    ProcessDefinitionNotFoundError,
)
from smyth.dispatcher.process import LambdaProcess
from smyth.dispatcher.type import ProcessDefinition
from smyth.utils import import_attribute

LOGGER = logging.getLogger(__name__)


class Dispatcher:
    def __init__(self, config: Config):
        self.config = config
        self.process_definitions = self.get_process_definitions(config)
        self.process_groups = self.build_process_groups(self.process_definitions)

    async def __call__(self, request: Request):
        return self.dispatch(request)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def stop(self):
        for process_group in self.process_groups.values():
            for process in process_group:
                process.stop()
                if process.is_alive():
                    process.terminate()
        for process_group in self.process_groups.values():
            for process in process_group:
                if process.is_alive():
                    process.join()

    def get_process_definitions(self, config: Config) -> dict[str, ProcessDefinition]:
        return {
            handler_config.url_path: ProcessDefinition(
                name=handler_name,
                handler_config=handler_config,
                event_data_generator=import_attribute(
                    handler_config.event_data_generator_path
                ),
                context_data_generator=import_attribute(
                    handler_config.context_data_generator_path
                ),
                url_path=compile_path(handler_config.url_path)[0],
                dispatch_strategy_class=import_attribute(
                    handler_config.dispatch_strategy_path
                ),
            )
            for handler_name, handler_config in config.handlers.items()
        }

    def build_process_groups(
        self, process_definitions: dict[str, ProcessDefinition]
    ) -> dict[str, list[LambdaProcess]]:
        process_groups: dict[str, list[LambdaProcess]] = {}
        for process_definition in process_definitions.values():
            process_groups[process_definition.name] = []
            for index in range(process_definition.handler_config.concurrency):
                process = LambdaProcess(
                    name=f"{process_definition.name}:{index}",
                    handler_config=process_definition.handler_config,
                )
                process_groups[process_definition.name].append(process)
        return process_groups

    def get_process_definition(self, path: str) -> ProcessDefinition:
        for path, process_def in self.process_definitions.items():
            if process_def.url_path.match(path):
                return process_def
        raise ProcessDefinitionNotFoundError(
            f"No process definition found for path {path}"
        )

    async def dispatch(self, request: Request):
        LOGGER.debug("Dispatching request %s", request.url.path)
        process_def = self.get_process_definition(request.url.path)
        process = process_def.dispatch_strategy_class(
            process_groups=self.process_groups
        ).get_process(process_def.name)
        if not process:
            raise NoAvailableProcessError(
                f"No available process for {process_def.name}"
            )
        if process.state == "COLD":
            await process.astart()

        event_data = await process_def.event_data_generator(request)
        context_data = await process_def.context_data_generator(
            request, process_def, process
        )

        return await process.asend(
            json.dumps({"event": event_data, "context": context_data})
        )
