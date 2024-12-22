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
                "smyth_handler_config": {
                    "concurrency": 1,
                    "context_data_function": ANY,
                    "event_data_function": ANY,
                    "lambda_handler_path": "tests.conftest.example_handler",
                    "log_level": "INFO",
                    "name": "test_handler",
                    "strategy_generator": ANY,
                    "timeout": None,
                    "url_path": re.compile("/test_handler"),
                    "env_overrides": {"TEST_ENV": "test"},
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
