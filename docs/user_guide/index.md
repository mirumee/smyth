# First Steps

Smyth is built to have minimal or no impact on the project you are working on. That said, it comes with features that allow you to customize Smyth to the needs of your Lambda project.

Following this guide will help you understand how to set up your development environment with Smyth.

## Example Application

Throughout this guide, we will use two lambda handlers as an example application.

```python title="my_project/src/my_app/handlers.py" linenums="1"
COUNT = 0

def order_handler(event, context):
    global COUNT
    COUNT += 1
    print(event, context)
    return {"statusCode": 200, "body": f"Orders requests: {COUNT}"}

def product_handler(event, context):
    global COUNT
    COUNT += 1
    print(event, context)
    return {"statusCode": 200, "body": f"Products requests: {COUNT}"}
```

These handlers do the exact same thing, and the global `COUNT` is there to illustrate how Smyth handles state between different requests (more about that in [concurrency](concurrency.md)).

??? question "What is the project's structure?"

    If this is in question, here is the example project's directory structure:

    ```
    myproject
    ├── pyproject.toml
    └── src
        └── my_app
            └── handlers.py
    ```

## Configuration

Now, in our project's `pyproject.toml`, we can set up Smyth to instruct how the Lambdas will be executed. This setup reflects how your Lambdas will be deployed on AWS behind, for example, an API Gateway.

```toml title="myproject/pyproject.toml" linenums="1" hl_lines="6-7 10-11"
[tool.smyth]
host = "0.0.0.0"  # (1)!
port = 8080

[tool.smyth.handlers.order_handler]
handler_path = "my_app.handlers.order_handler"
url_path = "/orders/{path:path}"

[tool.smyth.handlers.product_handler]
handler_path = "my_app.handlers.product_handler"
url_path = "/products/{path:path}"
```

1. Define the host and port on which you want Uvicorn to listen.

Under `tool.smyth.handlers`, you name and define your handlers. The only two required options are:

- `handler_path` - the Python path to the Lambda handler.
- `url_path` - the path with which the handler is to be reached by Starlette - uses [Starlette's URL resolving](https://www.starlette.io/routing/#path-parameters){target="_blank"}.

!!! tip "Custom Smyth Entrypoint"

    You don't have to use the TOML config - read more about [Custom Entrypoint](custom_entrypoint.md).

## Run It

At this point, you can start Smyth from your project's root directory:


<div class="termy" data-termynal="" data-ty-macos="" data-ty-title="bash" data-ty-lineDelay="100">
    <span data-ty="input" data-ty-prompt="$"> python -m smyth</span>
    <span data-ty>[14:12:00] INFO     [MainProcess] Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)                                 config.py:523</span>
    <span data-ty>           INFO     [MainProcess] Started reloader process [22786] using StatReload                                          basereload.py:79</span>
    <span data-ty>[14:12:00] DEBUG    [SpawnProcess-1] Using selector: KqueueSelector                                                     selector_events.py:64</span>
    <span data-ty>           INFO     [SpawnProcess-1] Started server process [22788]                                                              server.py:82</span>
    <span data-ty>           INFO     [SpawnProcess-1] Waiting for application startup.                                                                on.py:48</span>
    <span data-ty>           INFO     [SpawnProcess-1] Started process order_handler:0                                                              smyth.py:66</span>
    <span data-ty>           INFO     [SpawnProcess-1] Started process order_handler:1                                                              smyth.py:66</span>
    <span data-ty>           INFO     [SpawnProcess-1] Started process product_handler:0                                                            smyth.py:66</span>
    <span data-ty>           INFO     [SpawnProcess-1] Started process product_handler:1                                                            smyth.py:66</span>
    <span data-ty>           INFO     [SpawnProcess-1] Application startup complete.                                                                   on.py:62</span>
</div>


Visit [http://localhost:8080/orders/](http://localhost:8080/orders/){target="_blank"} to get the Order Handler response.
