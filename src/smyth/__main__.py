import logging
import logging.config
import os
from enum import Enum
from typing import Annotated, Optional

import typer
import uvicorn
from setproctitle import setproctitle

from smyth.config import get_config, get_config_dict, serialize_config
from smyth.utils import get_logging_config

app = typer.Typer()
config = get_config(get_config_dict())


LOGGER = logging.getLogger(__name__)


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@app.command()
def run(
    # typer does not handle union types
    smyth_starlette_app: Annotated[
        str,
        typer.Argument(
            help="Path to your SmythStarlette app (or factory with --factory)"
        ),  # noqa: UP007
    ] = "smyth.server.app:create_app",
    factory: Annotated[bool, typer.Option(help="Use factory for app creation")] = True,
    host: Annotated[Optional[str], typer.Option()] = config.host,  # noqa: UP007
    port: Annotated[Optional[int], typer.Option()] = config.port,  # noqa: UP007
    log_level: Annotated[
        Optional[LogLevel],  # noqa: UP007
        typer.Option(
            help=(
                "Override the log level specified in the configuration, "
                "only for the main process"
            )
        ),
    ] = LogLevel(config.log_level),
    quiet: Annotated[
        bool, typer.Option(help="Effectively the same as --log-level=ERROR")
    ] = False,
) -> None:
    if host:
        config.host = host
    if port:
        config.port = port
    if log_level:
        config.log_level = log_level.value
    if quiet:
        config.log_level = "ERROR"

    logging_config = get_logging_config(
        log_level=config.log_level, filter_path_prefix=config.smyth_path_prefix
    )

    setproctitle("smyth")
    os.environ["__SMYTH_CONFIG"] = serialize_config(config)

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
