from dataclasses import asdict
from typing import Any

from starlette.requests import Request

from smyth.dispatcher.process import LambdaProcess
from smyth.dispatcher.type import ProcessDefinition


async def generate_context_data(
    request: Request, process_def: ProcessDefinition, process: LambdaProcess
):
    """
    The data returned by this function is passed to the
    `smyth.runner.FaneContext` as kwargs.
    """
    context: dict[str, Any] = {
        "smyth": {
            "process": {
                "name": process.name,
                "state": process.state,
                "task_counter": process.task_counter,
                "last_used_timestamp": process.last_used_timestamp,
            },
            "process_def": {
                "name": process_def.name,
                "handler_config": asdict(process_def.handler_config),
            },
        }
    }
    if process_def.handler_config.timeout is not None:
        context["timeout"] = process_def.handler_config.timeout
    return context
