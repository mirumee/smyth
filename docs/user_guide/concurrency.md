# Concurrency

Smyth can also simulate the behavior of real Lambdas in terms of multiprocessing. For instance, every Lambda invocation can be run on a different machine, not holding the state between different runtimes. To simulate this, you can set the `concurrency` setting. Don't think of it in terms of web server performance - Smyth is not meant for production to demand high performance. Instead, consider it a method to keep you in check when developing your Lambda. It serves as a reminder that not everything can be stored in globals, and that in-memory cache might not persist between runs.

??? example "Cold vs warm starts"

    If we take our code with one handler:

    ```python linenums="1"
    COUNT = 0

    def order_handler(event, context):
        global COUNT
        COUNT += 1
        print(event, context)
        return {"statusCode": 200, "body": f"Orders requests: {COUNT}"}
    ```

    Upon a cold start, the code outside of the handler function (the `COUNT` declaration in this case) will be interpreted. After that, each warm run of that Lambda will maintain the state of the `COUNT`. If the load is high enough, AWS will run more Lambdas for you, which might start from a cold state.

To set up Smyth to run your handler in more than one subprocess, use the `concurrency` setting (by default it's `1`).

```toml title="myproject/pyproject.toml" linenums="1" hl_lines="4 9"
[tool.smyth.handlers.order_handler]
handler_path = "smyth_test_app.handlers.order_handler"
url_path = "/orders/{path:path}"
concurrency = 2

[tool.smyth.handlers.product_handler]
handler_path = "smyth_test_app.handlers.product_handler"
url_path = "/products/{path:path}"
concurrency = 2
strategy_function_path = "smyth.runner.strategy.round_robin"
```

## Dispatch Strategy

Dispatch strategy is controlled by a generator function that tells Smyth which subprocess from the pool of processes running a handler should be used. There are two built-in strategy functions:

- `smyth.runner.strategy.first_warm` - (the default) tries to act like AWS, using a warmed-up Lambda (handler) if available. It only thaws a cold one if there is nothing warm or they are busy. This strategy is not ideal as it relies on the state of the process which might have changed since the generator was asked for the process, but it's good enough for a one client (you, the developer) scenario.
- `smyth.runner.strategy.round_robin` - this one might keep you more in check as it picks the subprocess that was not used for the longest time, effectively using each subprocess one by one.

You can choose the strategy function (including your own, in the same way as you would an event or context generator) with the `strategy_function_path` setting.
