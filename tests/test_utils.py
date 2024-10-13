from smyth.utils import get_logging_config, import_attribute


def test_get_logging_config():
    logging_config = get_logging_config("DEBUG")
    assert logging_config["version"] == 1
    assert logging_config["disable_existing_loggers"] is False
    assert logging_config["filters"] == {}
    assert (
        logging_config["handlers"]["console"]["class"] == "smyth.utils.SmythRichHandler"
    )
    assert logging_config["handlers"]["console"]["markup"] is True
    assert logging_config["handlers"]["console"]["rich_tracebacks"] is True
    assert logging_config["handlers"]["console"]["filters"] == []
    assert logging_config["handlers"]["console"]["show_path"] is False
    assert logging_config["loggers"]["smyth"]["handlers"] == ["console"]
    assert logging_config["loggers"]["smyth"]["level"] == "DEBUG"
    assert logging_config["loggers"]["smyth"]["propagate"] is False
    assert logging_config["loggers"]["uvicorn"]["handlers"] == ["console"]
    assert logging_config["loggers"]["uvicorn"]["level"] == "DEBUG"
    assert logging_config["loggers"]["uvicorn"]["propagate"] is False

    logging_config = get_logging_config("INFO", "/smyth")
    assert (
        logging_config["filters"]["smyth_api_filter"]["smyth_path_prefix"] == "/smyth"
    )
    assert logging_config["handlers"]["console"]["filters"] == ["smyth_api_filter"]


def test_import_attribute():
    assert import_attribute("smyth.utils.get_logging_config") == get_logging_config
