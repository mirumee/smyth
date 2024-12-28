import pytest

from smyth.event import (
    generate_api_gw_v2_event_data,
    generate_lambda_invocation_event_data,
)

pytestmark = pytest.mark.anyio


async def test_generate_api_gw_v2_event_data(mocker):
    mock_request = mocker.Mock()
    mock_request.body = mocker.AsyncMock(return_value=b"")
    mock_request.headers = {}
    mock_request.query_params = {}
    mock_request.client.host = "127.0.0.1"
    mock_request.method = "GET"
    mock_request.url.path = "/test"
    mock_request.url.query = ""
    mock_request.url.scheme = "http"

    assert await generate_api_gw_v2_event_data(
        mock_request, mocker.Mock(), mocker.Mock()
    ) == {
        "version": "2.0",
        "rawPath": "/test",
        "body": "",
        "isBase64Encoded": False,
        "headers": {},
        "queryStringParameters": {},
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/test",
                "protocol": "http",
                "sourceIp": "127.0.0.1",
            },
            "routeKey": "GET /test",
            "accountId": "offlineContext_accountId",
            "stage": "$default",
        },
        "routeKey": "GET /test",
        "rawQueryString": "",
    }


async def test_generate_lambda_invokation_event_data(mocker):
    mock_request = mocker.Mock()
    mock_request.json = mocker.AsyncMock(return_value={"test": "test"})

    assert await generate_lambda_invocation_event_data(
        mock_request, mocker.Mock(), mocker.Mock()
    ) == {"test": "test"}
