from typing import Any

from starlette.requests import Request

from smyth.types import EventData, RunnerProcessProtocol, SmythHandler


async def generate_api_gw_v2_event_data(
    request: Request, smyth_handler: SmythHandler, process: RunnerProcessProtocol
) -> EventData:
    source_ip = None
    if request.client:
        source_ip = request.client.host
    return {
        "version": "2.0",
        "rawPath": request.url.path,
        "body": (await request.body()).decode("utf-8"),
        "isBase64Encoded": False,
        "headers": dict(request.headers),
        "queryStringParameters": dict(request.query_params),
        "requestContext": {
            "http": {
                "method": request.method,
                "path": request.url.path,
                "protocol": request.url.scheme,
                "sourceIp": source_ip,
            },
            "routeKey": f"{request.method} {request.url.path}",
            "accountId": "offlineContext_accountId",
            "stage": "$default",
        },
        "routeKey": f"{request.method} {request.url.path}",
        "rawQueryString": request.url.query,
    }


async def generate_lambda_invocation_event_data(
    request: Request, smyth_handler: SmythHandler, process: RunnerProcessProtocol
) -> Any:
    return await request.json()
