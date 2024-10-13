import pytest

from smyth.exceptions import NoAvailableProcessError
from smyth.runner.strategy import first_warm, round_robin
from smyth.types import SmythHandlerState


def test_round_robin():
    strat = round_robin("test_handler", {"test_handler": [1, 2, 3]})
    assert next(strat) == 1
    assert next(strat) == 2
    assert next(strat) == 3
    assert next(strat) == 1
    assert next(strat) == 2


def test_first_warm(mocker):
    mock_cold_process = mocker.Mock()
    mock_cold_process.state = SmythHandlerState.COLD
    mock_working_process = mocker.Mock()
    mock_working_process.state = SmythHandlerState.WORKING
    mock_warm_process = mocker.Mock()
    mock_warm_process.state = SmythHandlerState.WARM

    strat = first_warm(
        "test_handler",
        {"test_handler": [mock_working_process, mock_cold_process, mock_warm_process]},
    )

    assert next(strat) == mock_warm_process
    assert next(strat) == mock_warm_process
    assert next(strat) == mock_warm_process


def test_first_warm_no_warm(mocker):
    mock_cold_process = mocker.Mock()
    mock_cold_process.state = SmythHandlerState.COLD
    mock_working_process = mocker.Mock()
    mock_working_process.state = SmythHandlerState.WORKING
    mock_warm_process = mocker.Mock()
    mock_warm_process.state = SmythHandlerState.WARM

    strat = first_warm(
        "test_handler",
        {"test_handler": [mock_working_process, mock_cold_process, mock_cold_process]},
    )

    assert next(strat) == mock_cold_process
    assert next(strat) == mock_cold_process
    mock_working_process.state = SmythHandlerState.WARM
    assert next(strat) == mock_working_process


def test_first_warm_no_available(mocker):
    mock_working_process = mocker.Mock()
    mock_working_process.state = SmythHandlerState.WORKING

    strat = first_warm(
        "test_handler",
        {"test_handler": [mock_working_process]},
    )

    with pytest.raises(NoAvailableProcessError) as excinfo:
        next(strat)

    assert excinfo.errisinstance(NoAvailableProcessError)
