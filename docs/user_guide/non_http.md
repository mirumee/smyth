# Non-HTTP Invocation

You don't need Uvicorn and Starlette to use Smyth. Testing your Lambdas that handle events such as SQS, DynamoDB, etc., is also possible with Smyth. You can achieve this by creating an entrypoint script similar to the one in [Custom Entrypoint](custom_entrypoint.md).

## Example

In your `etc` directory, create a `smyth_run.py` file.

??? tip "Skip to the full file?"

    ```python title="my_project/etc/smyth_run.py" linenums="1"
    import asyncio

    from smyth.runner.strategy import round_robin
    from smyth.smyth import Smyth

    def my_handler(event, context):
        print(event["Records"][0]["body"], context.smyth["process"]["name"])

    EVENT_DATA = {
        "Records": [
            {
                "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
                "receiptHandle": "MessageReceiptHandle",
                "body": "Hello from SQS!",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1523232000000",
                    "SenderId": "123456789012",
                    "ApproximateFirstReceiveTimestamp": "1523232000001",
                },
                "messageAttributes": {},
                "md5OfBody": "7b270e59b47ff90a553787216d55d91d",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
                "awsRegion": "us-east-1",
            }
        ]
    }

    smyth = Smyth()

    smyth.add_handler(
        name="hello",
        path="/hello",
        lambda_handler_path="smyth_run.my_handler",
        timeout=60,
        concurrency=10,
        strategy_generator=round_robin,
    )

    async def main():
        handler = smyth.get_handler_for_name("hello")
        await asyncio.gather(
            *[
                smyth.invoke(
                    handler=handler,
                    event_data=EVENT_DATA,
                )
                for _ in range(20)
            ],
            return_exceptions=True,
        )

    if __name__ == "__main__":
        with smyth:
            asyncio.run(main())

    ```

### Import and Declare the Basics

Import `asyncio`, `smyth`, and your Lambda handler function.

```python title="my_project/etc/smyth_run.py" linenums="1"
import asyncio

from smyth.runner.strategy import round_robin
from smyth.smyth import Smyth

def my_handler(event, context):
    print(event["Records"][0]["body"], context.smyth["process"]["name"])
```

### Create the Event Data

This example comes from `sam local generate-event sqs receive-message`. Yours might be more complex.

```python title="my_project/etc/smyth_run.py" linenums="9"
EVENT_DATA = {
    "Records": [
        {
            "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
            "receiptHandle": "MessageReceiptHandle",
            "body": "Hello from SQS!",
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1523232000000",
                "SenderId": "123456789012",
                "ApproximateFirstReceiveTimestamp": "1523232000001",
            },
            "messageAttributes": {},
            "md5OfBody": "7b270e59b47ff90a553787216d55d91d",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
            "awsRegion": "us-east-1",
        }
    ]
}
```

### Instantiate Smyth and Add Handlers

Initialize Smyth and add your handlers.

```python title="my_project/etc/smyth_run.py" linenums="30"
smyth = Smyth()

smyth.add_handler(
    name="hello",
    path="/hello",
    lambda_handler_path="smyth_run.my_handler",
    timeout=60,
    concurrency=10,
    strategy_generator=round_robin,
)
```

### Prepare the Main Function

This part depends on what you want to achieve. Here we are trying to simulate a bunch of SQS messages quickly triggering a handler.

```python title="my_project/etc/smyth_run.py" linenums="41"
async def main():
    handler = smyth.get_handler_for_name("hello")
    await asyncio.gather(
        *[
            smyth.invoke(
                handler=handler,
                event_data=EVENT_DATA,
            )
            for _ in range(20)
        ],
        return_exceptions=True,
    )

if __name__ == "__main__":
    with smyth:
        asyncio.run(main())
```

### Run It

<div class="termy" data-termynal="" data-ty-macos="" data-ty-title="bash">
    <span data-ty="input" data-ty-prompt="$"> python etc/smyth_run.py</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:8</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:4</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:5</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:3</span>
    <span data-ty>Hello from SQS! hello:1</span>
    <span data-ty>Hello from SQS! hello:2</span>
    <span data-ty>Hello from SQS! hello:6</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:4</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:3</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:1</span>
    <span data-ty>Hello from SQS! hello:0</span>
    <span data-ty>Hello from SQS! hello:5</span>
    <span data-ty>Hello from SQS! hello:8</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:2</span>
    <span data-ty>Hello from SQS! hello:0</span>
    <span data-ty>Hello from SQS! hello:6</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:9</span>
    <span data-ty data-ty-delay="10">Hello from SQS! hello:9</span>
    <span data-ty>Hello from SQS! hello:7</span>
    <span data-ty>Hello from SQS! hello:7</span>
</div>
