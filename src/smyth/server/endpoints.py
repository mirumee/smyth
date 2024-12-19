import logging
from typing import Any

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from smyth.event import generate_lambda_invocation_event_data
from smyth.exceptions import LambdaInvocationError, LambdaTimeoutError, SubprocessError
from smyth.smyth import Smyth
from smyth.types import EventDataCallable, SmythHandler

LOGGER = logging.getLogger(__name__)


async def dispatch(
    smyth: Smyth,
    smyth_handler: SmythHandler,
    request: Request,
    event_data_function: EventDataCallable | None = None,
) -> Response:
    """
    Dispatches a request to Smyth and translates a Smyth
    response to a Starlette response.
    """
    try:
        result = await smyth.dispatch(
            smyth_handler, request, event_data_function=event_data_function
        )
    except LambdaInvocationError as error:
        return Response(str(error), status_code=status.HTTP_502_BAD_GATEWAY)
    except LambdaTimeoutError:
        return Response("Lambda timeout", status_code=status.HTTP_408_REQUEST_TIMEOUT)
    except SubprocessError as error:
        return Response(str(error), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not result:
        return Response(
            "No response", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        content=result.body,
        status_code=result.status_code,
        headers=result.headers,
    )


async def lambda_invoker_endpoint(request: Request) -> Response:
    smyth: Smyth = request.app.smyth
    smyth_handler = smyth.get_handler_for_request(request.url.path)
    return await dispatch(smyth, smyth_handler, request)


async def invocation_endpoint(request: Request) -> Response:
    smyth: Smyth = request.app.smyth
    function = request.path_params["function"]
    try:
        smyth_handler = smyth.get_handler_for_name(function)
    except KeyError:
        return Response(
            f"Function {function} not found", status_code=status.HTTP_404_NOT_FOUND
        )
    smyth_handler.event_data_function = generate_lambda_invocation_event_data
    return await dispatch(
        smyth,
        smyth_handler,
        request,
        event_data_function=generate_lambda_invocation_event_data,
    )


async def status_endpoint(request: Request) -> Response:
    smyth: Smyth = request.app.smyth

    response_data: dict[str, Any] = {
        "lambda handlers": {},
    }

    for process_group_name, process_group in smyth.processes.items():
        response_data["lambda handlers"][process_group_name] = {
            "processes": [],
        }
        for process in process_group:
            response_data["lambda handlers"][process_group_name]["processes"].append(
                {
                    "state": process.state,
                    "task_counter": process.task_counter,
                }
            )
    return JSONResponse(
        content=response_data,
        status_code=status.HTTP_200_OK,
    )
