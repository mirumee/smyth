import logging
import os
from contextlib import asynccontextmanager
from multiprocessing import set_start_method

from starlette.applications import Starlette

from smyth.config import deserialize_config
from smyth.dispatcher.dispatcher import Dispatcher
from smyth.endpoints import lambda_invoker_endpoint, status_endpoint

LOGGER = logging.getLogger(__name__)
set_start_method("spawn", force=True)


@asynccontextmanager
async def lifespan(app: "SmythApp"):
    config = deserialize_config(os.environ["_SMYTH_CONFIG"])
    with Dispatcher(
        config=config
    ) as dispatcher:
        app.dispatcher = dispatcher
        yield


class SmythApp(Starlette):
    dispatcher: Dispatcher

    def __init__(self, *args, **kwargs):
        config = deserialize_config(os.environ["_SMYTH_CONFIG"])
        super().__init__(debug=True, lifespan=lifespan, *args, **kwargs)
        self.add_route(f"{config.smyth_path_prefix}/api/status", status_endpoint, methods=["GET"])
        self.add_route(
            "/{path:path}",
            lambda_invoker_endpoint,
            methods=["GET", "POST", "PUT", "DELETE"],
        )


app = SmythApp()
