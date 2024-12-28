import pytest
from starlette.routing import Route

from smyth.context import generate_context_data
from smyth.event import generate_api_gw_v2_event_data
from smyth.runner.strategy import first_warm
from smyth.server.app import SmythStarlette, create_app, lifespan
from smyth.server.endpoints import (
    invocation_endpoint,
    lambda_invoker_endpoint,
    status_endpoint,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_get_config(mocker, config):
    return mocker.patch("smyth.server.app.get_config", return_value=config)


def test_create_app(mocker, mock_get_config):
    mock_smyth = mocker.Mock()
    mocker.patch("smyth.server.app.Smyth", autospec=True, return_value=mock_smyth)

    app = create_app()

    assert app.smyth == mock_smyth
    mock_smyth.add_handler.assert_has_calls(
        [
            mocker.call(
                name="order_handler",
                path=r"/test_handler",
                lambda_handler_path="tests.conftest.example_handler",
                timeout=None,
                event_data_function=generate_api_gw_v2_event_data,
                context_data_function=generate_context_data,
                log_level="DEBUG",
                concurrency=1,
                strategy_generator=first_warm,
                env_overrides={"TEST_ENV": "child", "ROOT_ENV": "root"},
            ),
            mocker.call(
                name="product_handler",
                path=r"/products/{path:path}",
                lambda_handler_path="tests.conftest.example_handler",
                timeout=None,
                event_data_function=generate_api_gw_v2_event_data,
                context_data_function=generate_context_data,
                log_level="DEBUG",
                concurrency=1,
                strategy_generator=first_warm,
                env_overrides={"TEST_ENV": "root", "ROOT_ENV": "root"},
            ),
        ]
    )


def test_smyth_starlette(mocker):
    mock_smyth = mocker.Mock()

    app = SmythStarlette(smyth=mock_smyth, smyth_path_prefix="/smyth")

    assert app.smyth == mock_smyth
    assert app.routes == [
        Route("/smyth/api/status", status_endpoint, methods=["GET", "HEAD"]),
        Route(
            "/2015-03-31/functions/{function:str}/invocations",
            invocation_endpoint,
            methods=["POST"],
        ),
        Route(
            "/{path:path}",
            lambda_invoker_endpoint,
            methods=["DELETE", "GET", "HEAD", "POST", "PUT"],
        ),
    ]


async def test_lifespan(mocker):
    mock_app = mocker.Mock()

    async with lifespan(mock_app):
        mock_app.smyth.start_runners.assert_called_once_with()

    mock_app.smyth.stop_runners.assert_called_once_with()

    mock_app = mocker.Mock()
    mock_app.smyth.start_runners.side_effect = Exception("Test")

    with pytest.raises(Exception):
        async with lifespan(mock_app):
            pass
