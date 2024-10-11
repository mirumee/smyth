import re
from unittest.mock import Mock

import pytest

from smyth.types import RunnerProcessProtocol, SmythHandler, SmythHandlerState


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
    )


def example_handler(event, context):
    return {"statusCode": 200, "body": "Hello, World!"}


@pytest.fixture
def mock_lambda_handler():
    return example_handler


@pytest.fixture
def mock_event_data_function():
    return Mock()


@pytest.fixture
def mock_context_data_function():
    return Mock()


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
