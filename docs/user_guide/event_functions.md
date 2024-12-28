# Event Generators

An event generator is a simple coroutine used by Smyth to transform a Starlette `Request` instance into an `event` dictionary that is eventually used when invoking the Lambda handler.

Smyth comes with two built-in event generators: `smyth.event.generate_api_gw_v2_event_data` (used by default) and `smyth.event.generate_lambda_invocation_event_data`, which is used in the [invocation endpoint](invoke.md).

The first one builds a minimal API Gateway Proxy V2 event to simulate a Lambda being triggered by one. The other deserializes the request body (assumes it's proper JSON) and returns just that.

## Custom Event Generators

### Example Generator

If you need to work with events not covered by Smyth, you can create and provide your own. Assuming a simplified API Gateway V1 event, you can create a generator like this:

```python title="my_project/src/smyth_utils/event.py" linenums="1"
from smyth.types import EventData, RunnerProcessProtocol, SmythHandler


async def generate_api_gw_v1_event_data(request: Request, smyth_handler: SmythHandler, process: RunnerProcessProtocol) -> EventData:
    source_ip = None
    if request.client:
        source_ip = request.client.host

    return {
        "resource": request.url.path,
        "path": request.url.path,
        "httpMethod": request.method,
        "headers": dict(request.headers),
        "queryStringParameters": dict(request.query_params),
        "pathParameters": {},  # You may need to populate this based on your routing
        "stageVariables": None,
        "requestContext": {
            "resourceId": "offlineContext_resourceId",
            "resourcePath": request.url.path,
            "httpMethod": request.method,
            "extendedRequestId": "offlineContext_extendedRequestId",
            "requestTime": "21/Nov/2020:20:13:27 +0000",
            "path": request.url.path,
            "accountId": "offlineContext_accountId",
            "protocol": request.url.scheme,
            "stage": "dev",
            "domainPrefix": "offlineContext_domainPrefix",
            "requestTimeEpoch": int(request.timestamp().timestamp() * 1000),
            "requestId": "offlineContext_requestId",
            "identity": {
                ...
            },
            "domainName": "offlineContext_domainName",
            "apiId": "offlineContext_apiId"
        },
        "body": (await request.body()).decode("utf-8"),
        "isBase64Encoded": False
    }
```

!!! warning "This is example code; a proper API Gateway V1 generator might need to be different."

### Configuration

```toml title="myproject/pyproject.toml" linenums="1" hl_lines="8"
[tool.smyth]
host = "0.0.0.0"
port = 8080

[tool.smyth.handlers.order_handler]
handler_path = "my_app.handlers.order_handler"
url_path = "/orders/{path:path}"
event_data_function_path = "smyth_utils.event.generate_api_gw_v1_event_data"

[tool.smyth.handlers.product_handler]
handler_path = "my_app.handlers.product_handler"
url_path = "/products/{path:path}"
```

Note that `smyth_utils` needs to be in your Python path.

From this point on, the `order_handler` will receive a different `event` than the `product_handler`.

## Limited Built-in Generators

We provided a limited number of generators because there are many possibilities for event simulation. Simulating DynamoDB streams or SQS events locally might be appealing, but we were unsure how these would be used in real-life scenarios. We'd love to hear from the community about this - please don't hesitate to report [:material-github: GitHub issues](https://github.com/mirumee/smyth/issues){target="_blank"} with proposals on what event generators we should include in Smyth.
