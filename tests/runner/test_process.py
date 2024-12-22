from queue import Empty

import pytest

from smyth.exceptions import LambdaHandlerLoadError, LambdaTimeoutError
from smyth.runner.fake_context import FakeLambdaContext
from smyth.runner.process import RunnerProcess
from smyth.types import (
    RunnerInputMessage,
    SmythHandlerState,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_setproctitle(mocker):
    return mocker.patch("smyth.runner.process.setproctitle")


@pytest.fixture
def mock_logging_dictconfig(mocker):
    return mocker.patch("logging.config.dictConfig")


@pytest.fixture
def runner_process():
    return RunnerProcess("test_process", "tests.conftest.example_handler")


def test_init_process(runner_process):
    assert runner_process.name == "test_process"
    assert runner_process.task_counter == 0
    assert runner_process.last_used_timestamp == 0
    assert runner_process.state == SmythHandlerState.COLD
    assert runner_process.lambda_handler_path == "tests.conftest.example_handler"
    assert runner_process.log_level == "INFO"


def test_stop_process(runner_process):
    runner_process.start()
    assert runner_process.is_alive() is True
    runner_process.stop()
    assert runner_process.is_alive() is False


@pytest.mark.skip(reason="This needs more thought")
def test_send_process(runner_process):
    pass


def test_run(mocker, mock_setproctitle, mock_logging_dictconfig, runner_process):
    mock_lambda_invoker__ = mocker.patch.object(
        runner_process, "lambda_invoker__", autospec=True
    )
    mock_get_logging_config = mocker.patch(
        "smyth.runner.process.get_logging_config", autospec=True
    )
    runner_process.run()
    mock_setproctitle.assert_called_once_with(f"smyth:{runner_process.name}")
    mock_logging_dictconfig.assert_called_once_with(
        mock_get_logging_config.return_value
    )
    mock_lambda_invoker__.assert_called_once()


def test_get_message(mocker, runner_process):
    mock_input_queue = mocker.patch.object(runner_process, "input_queue", autospec=True)
    mock_input_queue.get.side_effect = [
        RunnerInputMessage(type="smyth.lambda.invoke", event={}, context={}),
        Empty,
        RunnerInputMessage(type="smyth.lambda.invoke", event={}, context={}),
        RunnerInputMessage(type="smyth.stop"),
    ]

    messages = list(runner_process.get_message__())

    assert len(messages) == 2
    assert messages[0].type == "smyth.lambda.invoke"
    assert messages[1].type == "smyth.lambda.invoke"


def test_get_event(mocker, runner_process):
    assert (
        runner_process.get_event__(
            RunnerInputMessage(type="smyth.lambda.invoke", event={}, context={})
        )
        == {}
    )


def test_get_context(mocker, runner_process):
    assert isinstance(
        runner_process.get_context__(
            RunnerInputMessage(type="smyth.lambda.invoke", event={}, context={})
        ),
        FakeLambdaContext,
    )

    assert (
        runner_process.get_context__(
            RunnerInputMessage(type="smyth.lambda.invoke", event={}, context={})
        )._timeout
        == 6
    )


def test_import_handler(mocker, runner_process):
    mock_import_attribute = mocker.patch(
        "smyth.runner.process.import_attribute", autospec=True
    )

    runner_process.import_handler__("tests.conftest.example_handler", {}, {})
    mock_import_attribute.assert_called_once_with("tests.conftest.example_handler")

    mock_import_attribute.side_effect = AttributeError
    with pytest.raises(LambdaHandlerLoadError):
        runner_process.import_handler__("tests.conftest.example_handler", {}, {})

    mock_import_attribute.side_effect = ImportError
    with pytest.raises(LambdaHandlerLoadError):
        runner_process.import_handler__("tests.conftest.example_handler", {}, {})

    mock_import_attribute.side_effect = Exception
    with pytest.raises(Exception):
        runner_process.import_handler__("tests.conftest.example_handler", {}, {})


def test_set_status(runner_process):
    runner_process.set_status__(SmythHandlerState.COLD)
    assert runner_process.state == SmythHandlerState.COLD


def test_timeout_handler(runner_process):
    with pytest.raises(LambdaTimeoutError):
        runner_process.timeout_handler__(None, None)


def test_lambda_invoker(mocker, runner_process):
    mock_handler = mocker.Mock()
    mock_handler.return_value = {"statusCode": 200, "body": "Hello, World!"}
    mock_import_attribute = mocker.patch(
        "smyth.runner.process.import_attribute",
        autospec=True,
        return_value=mock_handler,
    )
    mock_signal = mocker.patch("signal.signal", autospec=True)
    mock_signal.side_effect = lambda signum, frame: None

    mocker.patch.object(runner_process, "output_queue", autospec=True)

    mocker.patch.object(
        runner_process,
        "get_message__",
        autospec=True,
        return_value=[
            RunnerInputMessage(
                type="smyth.lambda.invoke", event={"test": "1"}, context={}
            ),
            RunnerInputMessage(
                type="smyth.lambda.invoke", event={"test": "2"}, context={}
            ),
        ],
    )
    mocker.patch.object(
        runner_process,
        "get_event__",
        autospec=True,
        side_effect=[
            {"test": "1"},
            {"test": "2"},
        ],
    )
    mock_get_context__ = mocker.patch.object(
        runner_process, "get_context__", autospec=True
    )
    mock_set_status__ = mocker.patch.object(
        runner_process, "set_status__", autospec=True
    )

    runner_process.lambda_invoker__()
    assert mock_import_attribute.call_count == 1

    mock_set_status__.assert_has_calls(
        [
            mocker.call(SmythHandlerState.COLD),
            mocker.call(SmythHandlerState.WARM),
            mocker.call(SmythHandlerState.WORKING),
            mocker.call(SmythHandlerState.WORKING),
        ]
    )

    assert mock_handler.call_count == 2
    mock_handler.assert_has_calls(
        [
            mocker.call({"test": "1"}, mock_get_context__.return_value),
            mocker.call({"test": "2"}, mock_get_context__.return_value),
        ]
    )
