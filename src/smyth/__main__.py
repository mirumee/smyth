import logging
from typing import Annotated, Optional

import typer
import uvicorn

from smyth.config import get_config, get_config_dict

app = typer.Typer()
config = get_config(get_config_dict())

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "smyth_api_filter": {
            "()": "smyth.utils.SmythStatusRouteFilter",
            "smyth_path_prefix": config.smyth_path_prefix,
        },
    },
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler",
            "formatter": "default",
            "markup": True,
            "rich_tracebacks": True,
            "filters": ["smyth_api_filter"],
        },
    },
    "formatters": {
        "default": {
            "format": "[%(processName)s] %(message)s",
            "datefmt": "[%X]",
        },
    },
    "loggers": {
        "smyth": {
            "handlers": ["console"],
            "level": config.log_level,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": config.log_level,
            "propagate": False,
        },
    },
}
logging.config.dictConfig(logging_config)
LOGGER = logging.getLogger(__name__)


@app.command()
def run(
    smyth_starlette_app: Annotated[
        Optional[str], typer.Argument()  # noqa: UP007
    ] = None,  # typer does not handle union types
    smyth_starlette_app_factory: Annotated[
        str, typer.Argument()
    ] = "smyth.server.app:create_app",
    host: Annotated[Optional[str], typer.Option()] = config.host,  # noqa: UP007
    port: Annotated[Optional[int], typer.Option()] = config.port,  # noqa: UP007
    log_level: Annotated[Optional[str], typer.Option()] = config.log_level,  # noqa: UP007
):
    if smyth_starlette_app and smyth_starlette_app_factory:
        raise typer.BadParameter(
            "Only one of smyth_starlette_app or smyth_starlette_app_factory "
            "should be provided."
        )

    factory = False
    if smyth_starlette_app_factory:
        smyth_starlette_app = smyth_starlette_app_factory
        factory = True
    if not smyth_starlette_app:
        raise typer.BadParameter(
            "One of smyth_starlette_app or smyth_starlette_app_factory "
            "should be provided."
        )

    if host:
        config.host = host
    if port:
        config.port = port
    if log_level:
        config.log_level = log_level

    uvicorn.run(
        smyth_starlette_app,
        factory=factory,
        host=config.host,
        port=config.port,
        reload=True,
        log_config=logging_config,
        timeout_keep_alive=60 * 15,
        lifespan="on",
    )


if __name__ == "__main__":
    app()
