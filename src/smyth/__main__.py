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
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler",
            "formatter": "default",
            "markup": True,
            "rich_tracebacks": True,
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
@click.option("-h", "--host", default=None, help="Host to run server on.", type=str)
@click.option("-p", "--port", default=None, help="Port to run server on.", type=int)
@click.option("--only", default=None, help="Port to run server on.", multiple=True)
def run(host: str | None, port: int | None, only: list[str] | None):
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

    os.environ["_SMYTH_CONFIG"] = serialize_config(config)

    uvicorn.run(
        "smyth.server:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_config=logging_config,
    )


if __name__ == "__main__":
    cli()
