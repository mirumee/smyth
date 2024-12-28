# Environment

Smyth allows you to overwrite the environemnt variables that are passed to the handlers to better reflect the actual AWS Lambda environment while allowing you to change things while developing locally.


```toml title='pyproject.toml' linenums="1"
[tool.smyth]
host = "0.0.0.0"
port = 8080
...

[tool.smyth.env]
AWS_ENDPOINT = "http://localstack:4566"
AWS_LAMBDA_FUNCTION_VERSION = "$SMYTH"

[tool.smyth.handlers.my_special_version_handler]
handler_path = "mypyoject.app.my_special_version_handler"
url_path = "{path:path}"
...

[tool.smyth.handlers.my_special_version_handler.env]
AWS_LAMBDA_FUNCTION_VERSION = "34"
```

The config above allows you to set a specific env var for every defined handler and overwrite or set 
specific values for individual handlers. In the example every handler would receive the 
`AWS_ENDPOINT = "http://localstack:4566"` and `AWS_LAMBDA_FUNCTION_VERSION = "$SMYTH"` env vars with
the exception of `my_special_version_handler` which will have a different version.

## Fake context

The `smyth.runner.fake_context.FakeLambdaContext` class used by Smyth will also consume of of the environment variables.

## Default variables

In the table bellow you will find which keys are set by Smyth when a handler is being invoked. 
Smyth will look for the key in the following order:

1. the handler configuration `env` key
2. the smyth global configuration `env` key
3. `os.environ`
4. when none of the above contain the key the default value is assigned

| Key                                 | Default Value                                                          |
| ----------------------------------- | ---------------------------------------------------------------------- |
| `"_HANDLER"`                        | `self.lambda_handler_path`                                             |
| `"AWS_ACCESS_KEY_ID"`               | `"000000000000"`                                                       |
| `"AWS_SECRET_ACCESS_KEY"`           | `"test"`                                                               |
| `"AWS_SESSION_TOKEN"`               | `"test"`                                                               |
| `"AWS_DEFAULT_REGION"`              | `"eu-central-1"`                                                       |
| `"AWS_REGION"`                      | `"eu-central-1"`                                                       |
| `"AWS_EXECUTION_ENV"`               | `"AWS_Lambda_python{sys.version_info.major}.{sys.version_info.minor}"` |
| `"AWS_LAMBDA_FUNCTION_MEMORY_SIZE"` | `"128"`                                                                |
| `"AWS_LAMBDA_FUNCTION_NAME"`        | `self.name`                                                            |
| `"AWS_LAMBDA_FUNCTION_VERSION"`     | `"$LATEST"`                                                            |
| `"AWS_LAMBDA_INITIALIZATION_TYPE"`  | `"on-demand"`                                                          |
| `"AWS_LAMBDA_LOG_GROUP_NAME"`       | `"/aws/lambda/{self.name}"`                                            |
| `"AWS_LAMBDA_LOG_STREAM_NAME"`      | `"{strftime('%Y/%m/%d')}/[$LATEST]smyth_aws_lambda_log_stream_name"`   |
| `"AWS_LAMBDA_RUNTIME_API"`          | `"127.0.0.1:9001"`                                                     |
| `"AWS_XRAY_CONTEXT_MISSING"`        | `"LOG_ERROR"`                                                          |
| `"AWS_XRAY_DAEMON_ADDRESS"`         | `"127.0.0.1:2000"`                                                     |
