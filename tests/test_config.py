import json
import os
from dataclasses import asdict
from pathlib import Path

import pytest

from smyth.config import (
    HandlerConfig,
    get_config,
    get_config_dict,
    get_config_file_path,
    serialize_config,
)
from smyth.exceptions import ConfigFileNotFoundError


def test_get_config_file_path():
    assert get_config_file_path() == get_config_file_path("pyproject.toml")

    with pytest.raises(ConfigFileNotFoundError):
        get_config_file_path("not_existing.toml")


def test_get_config_dict(mocker):
    mock_toml = mocker.patch("smyth.config.toml.load")
    mock_get_config_file_path = mocker.patch(
        "smyth.config.get_config_file_path", return_value=Path("pyproject.toml")
    )

    assert get_config_dict() == mock_toml.return_value
    mock_toml.assert_called_once_with(mock_get_config_file_path.return_value)
    mock_get_config_file_path.assert_called_once_with()

    mock_get_config_file_path.reset_mock()
    mock_toml.reset_mock()
    mock_get_config_file_path.return_value = Path("other.toml")

    assert get_config_dict("other.toml") == mock_toml.return_value
    mock_toml.assert_called_once_with(mock_get_config_file_path.return_value)
    mock_get_config_file_path.assert_called_once_with("other.toml")


def test_get_config(config_toml_dict):
    config = get_config(config_toml_dict)

    assert config.host == "0.0.0.0"
    assert config.port == 8080
    assert config.handlers == {
        "order_handler": HandlerConfig(
            handler_path="tests.conftest.example_handler",
            url_path=r"/test_handler",
            env={"TEST_ENV": "child"},
        ),
        "product_handler": HandlerConfig(
            handler_path="tests.conftest.example_handler",
            url_path=r"/products/{path:path}",
        ),
    }
    assert config.log_level == "INFO"

    os.environ["__SMYTH_CONFIG"] = serialize_config(config)

    assert get_config(None) == config


def test_serialize_config(config):
    assert serialize_config(config) == json.dumps(asdict(config))


def test_get_env_overrides(config):
    handler_config = HandlerConfig(
        handler_path="tests.conftest.example_handler",
        url_path=r"/test_handler",
        env={"TEST_ENV": "test"},
    )

    assert handler_config.get_env_overrides(config) == {
        "ROOT_ENV": "root",
        "TEST_ENV": "test",
    }
