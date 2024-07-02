import re
from unittest.mock import ANY

from smyth.context import generate_context_data
from smyth.types import SmythHandlerState


async def test_generate_context_data(
    smyth_handler,
    mock_runner_process,
):
    assert await generate_context_data(None, smyth_handler, mock_runner_process) == {
        "smyth": {
            "handler": {
                "handler_config": {
                    "concurrency": 1,
                    "context_data_function": ANY,
                    "event_data_function": ANY,
                    "fake_coldstart": False,
                    "lambda_handler": ANY,
                    "log_level": "INFO",
                    "name": "test_handler",
                    "strategy_generator": ANY,
                    "timeout": None,
                    "url_path": re.compile("/test_handler"),
                },
                "name": "test_handler",
            },
            "process": {
                "last_used_timestamp": 0,
                "name": "test_process",
                "state": SmythHandlerState.COLD,
                "task_counter": 0,
            },
        },
    }
