import logging
from collections.abc import Callable, Iterable
from datetime import datetime
from importlib import import_module
from logging import LogRecord
from pathlib import Path
from typing import Any

from rich.console import Console, ConsoleRenderable, RenderableType
from rich.logging import RichHandler
from rich.table import Table
from rich.text import Text, TextType
from rich.traceback import Traceback

FormatTimeCallable = Callable[[datetime], Text]


def get_logging_config(
    log_level: str, filter_path_prefix: str | None = None
) -> dict[str, Any]:
    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {},
        "handlers": {
            "console": {
                "class": "smyth.utils.SmythRichHandler",
                "markup": True,
                "rich_tracebacks": True,
                "filters": [],
                "show_path": False,
            },
        },
        "loggers": {
            "smyth": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
        },
    }
    if filter_path_prefix:
        logging_config["filters"]["smyth_api_filter"] = {
            "()": "smyth.utils.SmythStatusRouteFilter",
            "smyth_path_prefix": filter_path_prefix,
        }
        logging_config["handlers"]["console"]["filters"].append("smyth_api_filter")
    return logging_config


class SmythStatusRouteFilter(logging.Filter):
    def __init__(self, name: str = "", smyth_path_prefix: str = "") -> None:
        super().__init__(name)
        self.smyth_path_prefix = smyth_path_prefix

    def filter(self, record: LogRecord) -> bool:
        return record.getMessage().find(self.smyth_path_prefix) == -1


class LogRender:  # pragma: no cover
    """
    Derived from `rich._log_render.LogRender`.
    """

    def __init__(
        self,
        show_time: bool = True,
        show_level: bool = False,
        show_path: bool = True,
        time_format: str | FormatTimeCallable = "[%X]",
        omit_repeated_times: bool = True,
        level_width: int | None = 8,
    ) -> None:
        self.show_time = show_time
        self.show_level = show_level
        self.show_path = show_path
        self.time_format = time_format
        self.omit_repeated_times = omit_repeated_times
        self.level_width = level_width
        self._last_time: Text | None = None

    def create_header_row(self, record: LogRecord) -> RenderableType:
        issuer = record.name.split(".")[0]

        if issuer == "smyth":
            issuer = "[bold yellow]Smyth[/]"
            process_name = record.processName
        elif issuer == "uvicorn":
            issuer = "[bold blue]Uvicorn[/]"
            process_name = f"Worker[{record.process}]"
        else:
            issuer = issuer.capitalize()
            process_name = record.processName

        return Text.from_markup(
            f"{issuer}:" f"[bold]{process_name}[/]",
            style="log.process",
        )

    def create_time_row(
        self,
        log_time: datetime | None,
        console: Console,
        time_format: str | FormatTimeCallable | None,
    ) -> RenderableType | None:
        log_time = log_time or console.get_datetime()
        time_format = time_format or self.time_format
        if callable(time_format):
            log_time_display = time_format(log_time)
        else:
            log_time_display = Text(log_time.strftime(time_format))
        if log_time_display == self._last_time and self.omit_repeated_times:
            return Text(" " * len(log_time_display))
        else:
            self._last_time = log_time_display
            return log_time_display

    def create_path_row(
        self, path: str, line_no: int | None, link_path: str | None
    ) -> RenderableType:
        path_text = Text()
        path_text.append(path, style=f"link file://{link_path}" if link_path else "")
        if line_no:
            path_text.append(":")
            path_text.append(
                f"{line_no}",
                style=f"link file://{link_path}#{line_no}" if link_path else "",
            )
        return path_text

    def configure_columns(self, record: LogRecord) -> tuple[bool, bool, bool]:
        full_width = getattr(record, "log_setting", None) == "console_full_width"

        if full_width:
            show_time = False
            show_level = False
            show_path = False
        else:
            show_time = self.show_time
            show_level = self.show_level
            show_path = self.show_path

        return show_time, show_level, show_path

    def __call__(
        self,
        record: LogRecord,
        console: "Console",
        renderables: Iterable["ConsoleRenderable"],
        log_time: datetime | None = None,
        time_format: str | FormatTimeCallable | None = None,
        level: TextType = "",
        path: str | None = None,
        line_no: int | None = None,
        link_path: str | None = None,
    ) -> "Table":
        from rich.containers import Renderables
        from rich.table import Table

        show_time, show_level, show_path = self.configure_columns(record)
        output = Table.grid(padding=(0, 1))
        output.expand = True
        output.add_column(justify="left", min_width=22)
        row: list[RenderableType] = []

        row.append(self.create_header_row(record))

        if show_time:
            output.add_column(style="log.time")
            create_time_row = self.create_time_row(log_time, console, time_format)
            if create_time_row:
                row.append(create_time_row)
        if show_level:
            output.add_column(style="log.level", width=self.level_width)
            row.append(level)

        output.add_column(ratio=1, style="log.message", overflow="fold")
        row.append(Renderables(renderables))

        if show_path and path:
            output.add_column(style="log.path")
            row.append(self.create_path_row(path, line_no, link_path))

        output.add_row(*row)
        return output


class SmythRichHandler(RichHandler):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.rich_render = LogRender(
            show_time=True,
            show_level=True,
            show_path=False,
            time_format="[%X]",
            omit_repeated_times=True,
            level_width=8,
        )

    def render(
        self,
        *,
        record: LogRecord,
        traceback: Traceback | None,
        message_renderable: "ConsoleRenderable",
    ) -> "ConsoleRenderable":
        path = Path(record.pathname).name
        level = self.get_level_text(record)
        time_format = None if self.formatter is None else self.formatter.datefmt
        log_time = datetime.fromtimestamp(record.created)

        log_renderable = self.rich_render(
            record=record,
            console=self.console,
            renderables=[message_renderable]
            if not traceback
            else [message_renderable, traceback],
            log_time=log_time,
            time_format=time_format,
            level=level,
            path=path,
            line_no=record.lineno,
            link_path=record.pathname if self.enable_link_path else None,
        )
        return log_renderable


def import_attribute(python_path: str) -> Any:
    module_name, handler_name = python_path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, handler_name)
