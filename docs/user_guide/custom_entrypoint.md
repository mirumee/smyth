# Custom Entrypoint

Starting from Smyth 0.4.0, you can use it outside of the provided entrypoint (`python -m smyth`). You can build your own entrypoint for Smyth, which would not require a TOML config but instead have a Python script living in your project like any other development helper script.

## Example

### Project Structure

Let's assume you have an `etc` directory that is not part of the final production package. Put your `smyth_conf.py` file there.

```hl_lines="3-4"
myproject
├── pyproject.toml
├── etc
│   └── smyth_conf.py
└── src
    └── my_app
        └── handlers.py
```

### Your Smyth Configuration

Here's an example `smyth_conf.py` file:

```python title="my_project/etc/smyth_conf.py" linenums="1"
import uvicorn
from smyth.server.app import SmythStarlette
from smyth.smyth import Smyth
from smyth.types import EventData, RunnerProcessProtocol, SmythHandler
from starlette.requests import Request


def my_handler(event, context):
    return {"statusCode": 200, "body": "Hello, World!"}

async def my_event_data_generator(request: Request, smyth_handler: SmythHandler, process: RunnerProcessProtocol) -> EventData:
    return {
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/hello",
            }
        }
    }

smyth = Smyth()

smyth.add_handler(
    name="hello",
    path="/hello",
    lambda_handler_path="smyth_run.my_handler",
    timeout=1,
    concurrency=1,
    event_data_function=my_event_data_generator,
)

app = SmythStarlette(smyth=smyth, smyth_path_prefix="/smyth")

if __name__ == "__main__":
    uvicorn.run("smyth_run:app", host="0.0.0.0", port=8080, reload=True)

```

Normally, the handler would be imported, but including the custom event generator in this file is a good use case. Use the `SmythStarlette` subclass of `Starlette` - it ensures all subprocesses are run at server start and killed on stop (using ASGI Lifetime). Create a Smyth instance and pass it to your `SmythStarlette` instance. Here, you can fine-tune logging, change Uvicorn settings, etc.

After that, run your script:

<div class="termy" data-termynal="" data-ty-macos="" data-ty-title="bash" data-ty-lineDelay="100">
    <span data-ty="input" data-ty-prompt="$"> python etc/smyth_conf.py</span>
    <span data-ty>INFO:     Will watch for changes in these directories: ['/Users/pkucmus/Development/mirumee/smyth_test_app']</span>
    <span data-ty>INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)</span>
    <span data-ty>INFO:     Started reloader process [29441] using StatReload</span>
    <span data-ty>INFO:     Started server process [29443]</span>
    <span data-ty>INFO:     Waiting for application startup.</span>
    <span data-ty>INFO:     Application startup complete.</span>
</div>
