# All Settings

Here's a list of all the settings, including those that are simpler but equally valuable, consolidated on one page:

## Smyth Settings

### Socket Binding

`host` - `str` (default: `"0.0.0.0"`) Used by Uvicorn to bind to an address.

`port` - `int` (default: `8080`) Used by Uvicorn as the bind port.

### Logging

`log_level` - `str` (default: `"INFO"`) Sets the logging level for the `uvicorn` and `smyth` logging handlers.

### Smyth Internals

`smyth_path_prefix` - `str` (default: `"/smyth"`) The path prefix used for Smyth's status endpoint. Change this if, for any reason, it collides with your path routing.

### Environment

`env` - `dict[str, str]` (default: `{}`) Environment variables to apply to every handler. Read more about [environment variables here](environment.md).

## Handler Settings

### Handler Path

`handler_path` - `str` (required) The Python path to your Lambda function.

### URL Path

`url_path` - `str` (required) The [Starlette routing](https://www.starlette.io/routing/#http-routing) path on which your handler will be exposed.

### Environment

`env` - `dict[str, str]` (default: `{}`) Environment variables to apply to this handler - keys defined here take precedence over the ones defined in `tool.smyth.env` and be otherwise merged. Read more about [environment variables here](environment.md).

### Customization

`event_data_function_path` - `str` (default: `"smyth.event.generate_api_gw_v2_event_data"`) Read more about [event functions here](event_functions.md).

`context_data_function_path` - `str` (default: `"smyth.context.generate_context_data"`) A function similar to the [event generator](event_functions.md), but it constructs the `context`, adding some metadata from Smyth's runtime. You can create and use your own.

### Behaviour

`timeout` - `float` (default: `None`, which means no timeout) The time in seconds after which the Lambda Handler raises a Timeout Exception, simulating Lambda's real-life timeouts.

`concurrency` - `int` (default: `1`) Read more about [concurrency here](concurrency.md).

`strategy_generator_path` - `str` (default: `"smyth.runner.strategy.first_warm"`) Read more about [dispatch strategies here](concurrency.md/#dispatch-strategy).

### Logging

`log_level` - `str` (default: `"INFO"`) Log level for Smyth's runner function, which is still part of Smyth but already running in the subprocess. Note that the logging of your Lambda handler code should be set separately.


## `pyproject.toml` example

```toml title='pyproject.toml' linenums="1"
[tool.smyth]
host = "0.0.0.0"
port = 8080
log_level = "INFO"
smyth_path_prefix = "/smyth"

[tool.smyth.handlers.lambda_handler]
handler_path = "myproject.app.lambda_handler"
url_path = "{path:path}"
timeout = 300
event_data_function_path = "smyth.event.generate_api_gw_v2_event_data"
context_data_function_path = "smyth.context.generate_context_data"
log_level = "DEBUG"
concurrency = 3
strategy_generator_path = "smyth.runner.strategy.first_warm"
```
