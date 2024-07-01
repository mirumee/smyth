# Lambda Invoke

An important aspect when working with Lambdas is the ability to invoke one like a remote function. The [Boto3 `Lambda.Client.invoke` function](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/invoke.html) is one way to run your Lambda code. Smyth recognizes the need to simulate that as well.

## Example

```python title="my_project/src/my_app/handlers.py" linenums="1"
import boto3

lambda_client = boto3.client(
    "lambda", 
    endpoint_url="http://localhost:8080"  # (1)!
)  

def order_handler(event, context):
    lambda_client.invoke(
        FunctionName="email_handler",  # (3)!
        InvocationType="Event",  # or RequestResponse
        Payload=b'{"to": "hello@mirumee.com", "subject": "Order made"}',
    )
    return {"statusCode": 200, "body": f"Orders requests: {COUNT}"}

def email_handler(event, context):
    print(event)  # (2)!
    return {"statusCode": 200, "body": f"Products requests: {COUNT}"}
```

1. Set the endpoint URL to your Smyth host and port.
2. The payload being sent to the handler: `{"to": "hello@mirumee.com", "subject": "Order made"}`.
3. Corresponds to the TOML config `[tool.smyth.handlers.email_handler]`.

## How It Works

No matter what `url_path` your handler is registered under in your config, every handler is also available via Smyth's `"/2015-03-31/functions/{function:str}/invocations"` URL. The difference from the `url_path` invocation is that when using the "direct invocation," the event generator is hardcoded to the `smyth.event.generate_lambda_invocation_event_data` function.

In the example above, the config might look like this:

```toml title="myproject/pyproject.toml" linenums="1" hl_lines="9 11"
[tool.smyth]
host = "0.0.0.0"
port = 8080

[tool.smyth.handlers.order_handler]
handler_path = "my_app.handlers.order_handler"
url_path = "/orders/{path:path}"

[tool.smyth.handlers.email_handler]
handler_path = "my_app.handlers.email_handler"
url_path = "/emails/{path:path}"
```

Line 9, which names the handler, is the important one here. Line 11 is required, but you don't have to use the HTTP request method to reach that handler.
