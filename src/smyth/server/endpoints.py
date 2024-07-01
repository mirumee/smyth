import logging
from typing import Any

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from smyth.event import generate_lambda_invokation_event_data
from smyth.exceptions import LambdaInvocationError, LambdaTimeoutError
from smyth.smyth import Smyth
from smyth.types import EventDataGenerator, SmythHandler

LOGGER = logging.getLogger(__name__)


async def dispatch(
    smyth: Smyth,
    handler: SmythHandler,
    request: Request,
    event_data_generator: EventDataGenerator | None = None,
):
    try:
        result = await smyth.dispatch(
            handler, request, event_data_generator=event_data_generator
        )
    except LambdaInvocationError as error:
        return Response(str(error), status_code=status.HTTP_502_BAD_GATEWAY)
    except LambdaTimeoutError:
        return Response("Lambda timeout", status_code=status.HTTP_408_REQUEST_TIMEOUT)

    if not result:
        return Response(
            "No response", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        content=result.get("body", result),
        status_code=result.get("statusCode", 200),
        headers=result.get("headers", {}),
    )


async def lambda_invoker_endpoint(request: Request):
    smyth: Smyth = request.app.smyth
    handler = smyth.get_handler_for_request(request.url.path)
    return await dispatch(smyth, handler, request)


async def invocation_endpoint(request: Request):
    smyth: Smyth = request.app.smyth
    function = request.path_params["function"]
    try:
        handler = smyth.get_handler_for_name(function)
    except KeyError:
        return Response(
            f"Function {function} not found", status_code=status.HTTP_404_NOT_FOUND
        )
    handler.event_data_generator = generate_lambda_invokation_event_data
    return await dispatch(
        smyth,
        handler,
        request,
        event_data_generator=generate_lambda_invokation_event_data,
    )


async def status_endpoint(request: Request):
    smyth: Smyth = request.app.smyth

    response_data: dict[str, Any] = {
        "lambda handlers": {},
    }

    for process_group_name, process_group in smyth.processes.items():
        response_data["lambda handlers"][process_group_name] = {  # type: ignore[index]
            "processes": [],
        }
        for process in process_group:
            response_data["lambda handlers"][process_group_name]["processes"].append(  # type: ignore[index]
                {
                    "state": process.state,
                    "task_counter": process.task_counter,
                }
            )
    return JSONResponse(
        content=response_data,
        status_code=status.HTTP_200_OK,
    )
