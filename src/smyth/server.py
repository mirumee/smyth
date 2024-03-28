import json
import logging
import os
from contextlib import asynccontextmanager
from multiprocessing import set_start_method

from starlette import status
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from smyth.config import deserialize_config
from smyth.process import LambdaProcess, ProcessDefinition, get_process_definitions
from smyth.schema import (
    LambdaExceptionResponse,
    LambdaHttpResponse,
)

LOGGER = logging.getLogger(__name__)
set_start_method("spawn", force=True)

config = deserialize_config(os.environ["_SMYTH_CONFIG"])

PROCESSES = get_process_definitions(config=config)


@asynccontextmanager
async def lifespan(app: Starlette):
    LOGGER.info("Starting lambda processes")
    started_processes: list[LambdaProcess] = []
    for process_def in PROCESSES:
        process_def.process.start()
        started_processes.append(process_def.process)
        LOGGER.info("[blue]%s[/blue] started and listening for events", process_def.process.name)
    try:
        yield
    finally:
        for process in started_processes:
            process.terminate()
            process.join()
        LOGGER.info("All lambda processes terminated")


def get_process_definition(path: str) -> ProcessDefinition | None:
    for process_def in PROCESSES:
        if process_def.url_path.match(path):
            return process_def
    return None


async def lambda_invoker_endpoint(request: Request):
    process_def = get_process_definition(request.url.path)

    if not process_def:
        return Response(
            "No lambda handler for that path", status_code=status.HTTP_404_NOT_FOUND
        )
    
    LOGGER.info(
        "Matched process %s for path %s", process_def.process.name, request.url.path
    )

    event_data = await process_def.event_data_generator(request)
    context_data = await process_def.context_data_generator(
        request, process_def.timeout
    )

    result = process_def.process.send(
        json.dumps({"event": event_data, "context": context_data})
    )
    if not result:
        return Response("No response", status_code=status.HTTP_408_REQUEST_TIMEOUT)

    if isinstance(result.response, LambdaExceptionResponse):
        return JSONResponse(
            content=result.response.model_dump(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    elif isinstance(result.response, LambdaHttpResponse):
        return Response(
            content=result.response.body,
            status_code=result.response.status_code,
            headers=result.response.headers,
        )


app = Starlette(
    debug=True,
    lifespan=lifespan,
    routes=[
        Route(
            "/{path:path}",
            lambda_invoker_endpoint,
            methods=["GET", "POST", "PUT", "DELETE"],
        ),
    ],
)
