import pytest

from smyth.exceptions import ProcessDefinitionNotFoundError
from smyth.runner.strategy import first_warm
from smyth.smyth import Smyth
from smyth.types import SmythHandlerState

pytestmark = pytest.mark.anyio


@pytest.fixture
def smyth(mock_event_data_function, mock_context_data_function):
    smyth = Smyth()
    smyth.add_handler(
        name="test_handler",
        path="/test_handler",
        lambda_handler_path="tests.conftest.example_handler",
        timeout=1,
        event_data_function=mock_event_data_function,
        context_data_function=mock_context_data_function,
        log_level="DEBUG",
        concurrency=1,
        strategy_generator=first_warm,
    )
    return smyth


def test_smyth_add_handler(smyth, mock_event_data_function, mock_context_data_function):
    handler = smyth.get_handler_for_name("test_handler")
    assert handler.name == "test_handler"
    assert handler.url_path.match("/test_handler")
    assert handler.lambda_handler_path == "tests.conftest.example_handler"
    assert handler.event_data_function == mock_event_data_function
    assert handler.context_data_function == mock_context_data_function
    assert handler.strategy_generator == first_warm
    assert handler.timeout == 1
    assert handler.log_level == "DEBUG"
    assert handler.concurrency == 1


def test_context_enter_exit(mocker):
    smyth = Smyth()
    mocker.patch.object(smyth, "start_runners")
    mocker.patch.object(smyth, "stop_runners")
    with smyth:
        pass
    assert smyth.start_runners.called
    assert smyth.stop_runners.called


def test_start_stop_runners(smyth):
    smyth.start_runners()
    assert smyth.processes["test_handler"][0].state == SmythHandlerState.COLD
    assert smyth.processes["test_handler"][0].task_counter == 0
    smyth.stop_runners()


def test_get_handler_for_request(smyth):
    handler = smyth.get_handler_for_request("/test_handler")
    assert handler.name == "test_handler"

    with pytest.raises(ProcessDefinitionNotFoundError):
        smyth.get_handler_for_request("/test_handler_2")


async def test_smyth_dispatch(
    smyth, mocker, mock_event_data_function, mock_context_data_function
):
    mock_asend = mocker.patch("smyth.runner.process.RunnerProcess.asend")
    mock_request = mocker.Mock()
    mock_request.method = "GET"
    mock_request.url.path = "/test_handler"

    with smyth:
        response = await smyth.dispatch(
            smyth.get_handler_for_name("test_handler"),
            mock_request,
        )

    assert mock_asend.await_args[0][0].type == "smyth.lambda.invoke"
    assert mock_asend.await_args[0][0].event == await mock_event_data_function()
    assert mock_asend.await_args[0][0].context == await mock_context_data_function()
    assert response == mock_asend.return_value


async def test_invoke(
    smyth, mocker, mock_event_data_function, mock_context_data_function
):
    mock_asend = mocker.patch("smyth.runner.process.RunnerProcess.asend")
    event_data = {"test": "data"}

    with smyth:
        response = await smyth.invoke(
            smyth.get_handler_for_name("test_handler"),
            event_data,
        )

    assert mock_asend.await_args[0][0].type == "smyth.lambda.invoke"
    assert mock_asend.await_args[0][0].event == event_data
    assert mock_asend.await_args[0][0].context == await mock_context_data_function()
    assert response == mock_asend.return_value
