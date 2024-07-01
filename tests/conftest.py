import re
from unittest.mock import Mock

import pytest

from smyth.types import RunnerProcessProtocol, SmythHandler, SmythHandlerState


@pytest.fixture
def smyth_handler(
    mock_lambda_handler,
    mock_event_data_generator,
    mock_context_data_generator,
    mock_strategy_function,
):
    return SmythHandler(
        name="test_handler",
        url_path=re.compile(r"/test_handler"),
        lambda_handler=mock_lambda_handler,
        event_data_generator=mock_event_data_generator,
        context_data_generator=mock_context_data_generator,
        strategy_function=mock_strategy_function,
    )


@pytest.fixture
def mock_lambda_handler():
    return Mock()


@pytest.fixture
def mock_event_data_generator():
    return Mock()


@pytest.fixture
def mock_context_data_generator():
    return Mock()


@pytest.fixture
def mock_strategy_function():
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
