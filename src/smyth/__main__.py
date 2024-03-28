import logging
import logging.config
import os

import click
import uvicorn

from smyth.config import get_config, get_config_dict, serialize_config

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
    "root": {
        "handlers": ["console"],
        "level": config.log_level,
    },
}
logging.config.dictConfig(logging_config)
LOGGER = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command()
@click.option("-h", "--host", default=None, help=f"Bind socket to this host. [default: {config.host}]", type=str)
@click.option("-p", "--port", default=None, help=f"Bind socket to this port. [default: {config.port}]", type=int)
@click.option("--only", default=None, help="Run only the handler of this name. [list]", multiple=True)
@click.option("--log-level", default=None, help=f"Log level. [default: {config.log_level}]", type=str)
def run(host: str | None, port: int | None, only: list[str] | None, log_level: str | None):
    LOGGER.info("Starting [blue bold]Smyth[/]")

    if only:
        config.handlers = {
            handler_name: handler_config
            for handler_name, handler_config in config.handlers.items()
            if handler_name in only
        }
        LOGGER.info(
            "[yellow][bold]Only[/bold] running handlers:[/yellow] [blue]%s[/blue]", 
            ", ".join(
                [handler for handler in config.handlers.keys()]
            )
        )

    if host:
        config.host = host
    if port:
        config.port = port
    if log_level:
        config.log_level = log_level

    os.environ["_SMYTH_CONFIG"] = serialize_config(config)

    uvicorn.run(
        "smyth.app:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_config=logging_config,
        timeout_keep_alive=60 * 15,
    )


if __name__ == "__main__":
    cli()
