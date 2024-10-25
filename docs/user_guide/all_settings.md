# All Settings

Here's a list of all the settings, including those that are simpler but equally valuable, consolidated on one page:

## Smyth Settings

### Host

`host` - `str` (default: `"0.0.0.0"`) Used by Uvicorn to bind to an address.

### Port

`port` - `int` (default: `8080`) Used by Uvicorn as the bind port.

### Log Level

`log_level` - `str` (default: `"INFO"`) Sets the logging level for the `uvicorn` and `smyth` logging handlers.

### Smyth Path Prefix

`smyth_path_prefix` - `str` (default: `"/smyth"`) The path prefix used for Smyth's status endpoint. Change this if, for any reason, it collides with your path routing.

## Handler Settings

### Handler Path

`handler_path` - `str` (required) The Python path to your Lambda function.

### URL Path

`url_path` - `str` (required) The Starlette routing path on which your handler will be exposed.

### Timeout

`timeout` - `float` (default: `None`, which means no timeout) The time in seconds after which the Lambda Handler raises a Timeout Exception, simulating Lambda's real-life timeouts.

### Event Data Function

`event_data_function_path` - `str` (default: `"smyth.event.generate_api_gw_v2_event_data"`) Read more about [event functions here](event_functions.md).

### Context Data Function

`context_data_function_path` - `str` (default: `"smyth.context.generate_context_data"`) A function similar to the [event generator](event_functions.md), but it constructs the `context`, adding some metadata from Smyth's runtime. You can create and use your own.

### Log Level

`log_level` - `str` (default: `"INFO"`) Log level for Smyth's runner function, which is still part of Smyth but already running in the subprocess. Note that the logging of your Lambda handler code should be set separately.

### Concurrency

`concurrency` - `int` (default: `1`) Read more about [concurrency here](concurrency.md).

### Strategy Generator

`strategy_generator_path` - `str` (default: `"smyth.runner.strategy.first_warm"`) Read more about [dispatch strategies here](concurrency.md/#dispatch-strategy).
