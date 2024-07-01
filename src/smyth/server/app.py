import logging
from contextlib import asynccontextmanager
from multiprocessing import set_start_method

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
async def lifespan(app: "SmythStarlette"):
    app.smyth.start_runners()
    yield
    app.smyth.stop_runners()


class SmythStarlette(Starlette):
    smyth: Smyth

    def __init__(self, smyth: Smyth, smyth_path_prefix: str, *args, **kwargs):
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


def create_app():
    config = get_config(get_config_dict())

    smyth = Smyth()

    for handler_name, handler_config in config.handlers.items():
        smyth.add_handler(
            name=handler_name,
            path=handler_config.url_path,
            lambda_handler=import_attribute(handler_config.handler_path),
            timeout=handler_config.timeout,
            event_data_generator=import_attribute(
                handler_config.event_data_generator_path
            ),
            context_data_generator=import_attribute(
                handler_config.context_data_generator_path
            ),
            fake_coldstart=handler_config.fake_coldstart,
            log_level=handler_config.log_level,
            concurrency=handler_config.concurrency,
            strategy_function=import_attribute(handler_config.strategy_function_path),
        )

    app = SmythStarlette(smyth=smyth, smyth_path_prefix=config.smyth_path_prefix)

    return app
