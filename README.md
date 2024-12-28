# Smyth

<div align="center">
<img src="https://github.com/mirumee/smyth/raw/main/docs/assets/logo_white_small.svg" alt="Smyth Logo" width="300" role="img">

[![docs](https://img.shields.io/badge/Docs-Smyth-f5c03b.svg?style=flat&logo=materialformkdocs)](https://mirumee.github.io/smyth/)
![pypi](https://img.shields.io/pypi/v/smyth?style=flat)
![licence](https://img.shields.io/pypi/l/smyth?style=flat)
![pypi downloads](https://img.shields.io/pypi/dm/smyth?style=flat)
![pyversion](https://img.shields.io/pypi/pyversions/smyth?style=flat)
</div>

Smyth is a tool designed to enhance your AWS Lambda development experience by mocking an AWS Lambda environment on your **local machine**. It is a pure Python tool that allows for easy customization and state persistence, making your Lambda development more efficient and developer-friendly. 

## Features

- **Pure Python**: Entirely written in Python, allowing flexibility to tailor it to your specific requirements.
- **Customizability**: Modify both the `event` and `context` data structures as needed.
- **State Persistence**: Simulates both cold and warm starts, retaining state across invocations, mimicking actual AWS Lambda behavior.
- **Efficiency**: Streamlined and efficient, relying solely on Python for code execution.
- **Inspired by Serverless Framework**: Designed with insights from the Serverless framework, effectively managing serverless applications.
- **Developer-Friendly**: Integrates seamlessly with common development tools and practices, such as PDB, iPDB, VSCode debugging, and .env file support.

## Installation

Install Smyth as a development dependency using Poetry or pip:

### Poetry
```bash
poetry add --group dev smyth
```

### pip
```bash
pip install smyth
```

Define the following settings in your Lambda project's `pyproject.toml` file:

```toml
[tool.smyth]
host = "0.0.0.0"
port = 8080

[tool.smyth.handlers.saleor_handler]
handler_path = "my_project.handlers.saleor.handler.saleor_http_handler"
url_path = "/saleor/{path:path}"
```

> [!TIP] 
> Check the [documentation](https://mirumee.github.io/smyth/user_guide/all_settings/) for more configuration options.

Run Smyth with:
```bash
python -m smyth
```

## Working with Docker

Assuming you have this already installed by Poetry you can use the `Dockerfile.example` and `docker-compose.example.yml` files from this repository to get started.

## Working with VS Code

To utilize the VS Code debugger with the Smyth tool, you can set up your `launch.json` configuration file as follows. This setup will enable you to debug your Lambda functions directly within VS Code, providing a seamless development experience.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Module",
            "type": "debugpy",
            "request": "launch",
            "module": "smyth",
            "args": ["run"],
        }
    ]
}
```

## Caveats

The combination of Uvicorn reload process and HTTP server process with what is being done with the Lambda processes is tricky. If a Lambda process is doing something and the HTTP server is killed in the wrong moment it's likely going to bork your terminal. This is not solved yet. It's best to use in a Docker container or have the ability to `kill -9 {PID of the Uvicorn reload process}` at hand.

## Name

This name blends "Smith" (as in a blacksmith, someone who works in a forge) with "Py" for Python, altering the spelling to "Smyth". Blacksmiths are craftsmen who work with metal in a forge, shaping it into desired forms. Similarly, "Smyth" suggests a tool that helps developers craft and shape their serverless projects with the precision and skill of a smith, but in the realm of Python programming. This name retains the essence of craftsmanship and transformation inherent in a forge while being associated with Python.

# Crafted with ❤️ by Mirumee Software hello@mirumee.com
