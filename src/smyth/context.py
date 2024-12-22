from dataclasses import asdict
from typing import Any

from starlette.requests import Request

from smyth.types import ContextData, RunnerProcessProtocol, SmythHandler


async def generate_context_data(
    request: Request | None, smyth_handler: SmythHandler, process: RunnerProcessProtocol
) -> ContextData:
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
            "handler": {
                "name": smyth_handler.name,
                "smyth_handler_config": asdict(smyth_handler),
            },
        }
    }
    if smyth_handler.timeout is not None:
        context["timeout"] = smyth_handler.timeout
    return context
