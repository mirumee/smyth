import pytest
from starlette.testclient import TestClient

from smyth.exceptions import LambdaInvocationError, LambdaTimeoutError, SubprocessError
from smyth.server.app import SmythStarlette
from smyth.server.endpoints import dispatch
from smyth.types import LambdaResponse

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_smyth_dispatch(mocker):
    return mocker.AsyncMock()


@pytest.fixture
def mock_smyth(mocker, mock_smyth_dispatch):
    smyth = mocker.Mock()
    smyth.handlers = {
        "order_handler": mocker.Mock(name="order_handler"),
        "product_handler": mocker.Mock(name="product_handler"),
    }
    smyth.processes = {
        "order_handler": [
            mocker.Mock(name="process1", task_counter=0, state="cold"),
        ],
        "product_handler": [
            mocker.Mock(name="process2", task_counter=0, state="cold"),
            mocker.Mock(name="process3", task_counter=0, state="cold"),
        ],
    }
    smyth.dispatch = mock_smyth_dispatch
    return smyth


@pytest.fixture
def app(mock_smyth):
    return SmythStarlette(smyth=mock_smyth, smyth_path_prefix="/smyth")


@pytest.fixture
def test_client(app):
    return TestClient(app)


@pytest.mark.parametrize(
    ("side_effect", "expected_status_code", "expected_body"),
    [
        (None, 200, b"Hello, World!"),
        (LambdaInvocationError("Test error"), 502, b"Test error"),
        (LambdaTimeoutError("Test error"), 408, b"Lambda timeout"),
        (SubprocessError("Test error"), 500, b"Test error"),
    ],
)
async def test_dispatch(
    mocker,
    mock_smyth,
    mock_smyth_dispatch,
    side_effect,
    expected_status_code,
    expected_body,
):
    mock_request = mocker.Mock()
    mock_event_data_function = mocker.Mock()
    mock_smyth_dispatch.return_value = LambdaResponse(
        body="Hello, World!",
        status_code=200,
        headers={},
    )
    mock_smyth_dispatch.side_effect = side_effect
    response = await dispatch(
        smyth=mock_smyth,
        smyth_handler=mock_smyth.handlers["order_handler"],
        request=mock_request,
        event_data_function=mock_event_data_function,
    )
    assert response.status_code == expected_status_code
    assert response.body == expected_body


def test_status_endpoint(test_client):
    response = test_client.get("/smyth/api/status")
    assert response.status_code == 200
    assert response.json() == {
        "lambda handlers": {
            "order_handler": {
                "processes": [
                    {
                        "state": "cold",
                        "task_counter": 0,
                    }
                ]
            },
            "product_handler": {
                "processes": [
                    {
                        "state": "cold",
                        "task_counter": 0,
                    },
                    {
                        "state": "cold",
                        "task_counter": 0,
                    },
                ]
            },
        },
    }


def test_invocation_endpoint(test_client, mock_smyth, mock_smyth_dispatch):
    mock_smyth_dispatch.return_value = LambdaResponse(
        body="Hello, World!",
        status_code=200,
        headers={},
    )
    response = test_client.post(
        "/2015-03-31/functions/order_handler/invocations",
        json={"test": "test"},
    )
    assert response.status_code == 200
    assert response.text == "Hello, World!"
