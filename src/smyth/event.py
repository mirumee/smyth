from starlette.requests import Request


async def generate_event_data(request: Request):
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
