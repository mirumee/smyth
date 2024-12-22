import re
from unittest.mock import AsyncMock, Mock

import pytest

from smyth.config import Config
from smyth.types import RunnerProcessProtocol, SmythHandler, SmythHandlerState


@pytest.fixture(autouse=True)
def anyio_backend():
    return "asyncio", {"use_uvloop": True}


@pytest.fixture
def smyth_handler(
    mock_lambda_handler,
    mock_event_data_function,
    mock_context_data_function,
    mock_strategy_generator,
):
    return SmythHandler(
        name="test_handler",
        url_path=re.compile(r"/test_handler"),
        lambda_handler_path="tests.conftest.example_handler",
        event_data_function=mock_event_data_function,
        context_data_function=mock_context_data_function,
        strategy_generator=mock_strategy_generator,
        env_overrides={
            "TEST_ENV": "test",
        },
    )


@pytest.fixture
def config_toml_dict():
    return {
        "tool": {
            "smyth": {
                "host": "0.0.0.0",
                "port": 8080,
                "env": {"ROOT_ENV": "root", "TEST_ENV": "root"},
                "handlers": {
                    "order_handler": {
                        "handler_path": "tests.conftest.example_handler",
                        "url_path": "/test_handler",
                        "env": {"TEST_ENV": "child"},
                    },
                    "product_handler": {
                        "handler_path": "tests.conftest.example_handler",
                        "url_path": "/products/{path:path}",
                    },
                },
                "log_level": "INFO",
            }
        }
    }


@pytest.fixture
def config(config_toml_dict):
    return Config.from_dict(config_toml_dict["tool"]["smyth"])


def example_handler(event, context):
    return {"statusCode": 200, "body": "Hello, World!"}


@pytest.fixture
def mock_lambda_handler():
    return example_handler


@pytest.fixture
def mock_event_data_function():
    return AsyncMock(return_value={"key": "value"})


@pytest.fixture
def mock_context_data_function():
    return AsyncMock(return_value={"key": "value"})


@pytest.fixture
def mock_strategy_generator():
    return Mock()


@pytest.fixture
def mock_runner_process():
    mock = Mock(
        spec=RunnerProcessProtocol,
    )
    mock.name = "test_process"
    mock.task_counter = 0
    mock.last_used_timestamp = 0
    mock.state = SmythHandlerState.COLD
    return mock
