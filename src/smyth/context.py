from dataclasses import asdict
from typing import Any

from starlette.requests import Request

from smyth.types import RunnerProcessProtocol, SmythHandler


async def generate_context_data(
    request: Request, handler: SmythHandler, process: RunnerProcessProtocol
):
    """
    The data returned by this function is passed to the
    `smyth.runner.FaneContext` as kwargs.
    """
    asdict(handler)
    context: dict[str, Any] = {
        "smyth": {
            "process": {
                "name": process.name,
                "state": process.state,
                "task_counter": process.task_counter,
                "last_used_timestamp": process.last_used_timestamp,
            },
            "handler": {
                "name": handler.name,
                "handler_config": asdict(handler),
            },
        }
    }
    if handler.timeout is not None:
        context["timeout"] = handler.timeout
    return context
