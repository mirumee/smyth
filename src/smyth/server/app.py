import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from multiprocessing import set_start_method
from typing import Any

from starlette.applications import Starlette

from smyth.config import get_config, get_config_dict
from smyth.server.endpoints import (
    invocation_endpoint,
    lambda_invoker_endpoint,
    status_endpoint,
)
from smyth.smyth import Smyth
from smyth.utils import import_attribute

LOGGER = logging.getLogger(__name__)
set_start_method("spawn", force=True)


@asynccontextmanager
async def lifespan(app: "SmythStarlette") -> AsyncGenerator[None, None]:
    try:
        app.smyth.start_runners()
    except Exception as error:
        LOGGER.error("Error starting runners: %s", error)
        raise
    yield
    app.smyth.stop_runners()


class SmythStarlette(Starlette):
    smyth: Smyth

    def __init__(self, smyth: Smyth, smyth_path_prefix: str, *args: Any, **kwargs: Any):
        self.smyth = smyth
        kwargs["lifespan"] = lifespan
        super().__init__(*args, **kwargs)
        self.add_route(
            f"{smyth_path_prefix}/api/status", status_endpoint, methods=["GET"]
        )
        self.add_route(
            "/2015-03-31/functions/{function:str}/invocations",
            invocation_endpoint,
            methods=["POST"],
        )
        self.add_route(
            "/{path:path}",
            lambda_invoker_endpoint,
            methods=["GET", "POST", "PUT", "DELETE"],
        )


def create_app() -> SmythStarlette:
    LOGGER.debug("Creating app")
    config = get_config(get_config_dict())

    smyth = Smyth()

    for handler_name, handler_config in config.handlers.items():
        smyth.add_handler(
            name=handler_name,
            path=handler_config.url_path,
            lambda_handler_path=handler_config.handler_path,
            timeout=handler_config.timeout,
            event_data_function=import_attribute(
                handler_config.event_data_function_path
            ),
            context_data_function=import_attribute(
                handler_config.context_data_function_path
            ),
            log_level=handler_config.log_level,
            concurrency=handler_config.concurrency,
            strategy_generator=import_attribute(handler_config.strategy_generator_path),
            env_overrides=handler_config.get_env_overrides(config),
        )

    app = SmythStarlette(smyth=smyth, smyth_path_prefix=config.smyth_path_prefix)

    return app
