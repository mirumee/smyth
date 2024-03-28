import logging

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from smyth.dispatcher.dispatcher import Dispatcher
from smyth.dispatcher.exceptions import DestroyedOnLoadError, LambdaTimeoutError
from smyth.schema import (
    LambdaExceptionResponse,
    LambdaHttpResponse,
)

LOGGER = logging.getLogger(__name__)


async def lambda_invoker_endpoint(request: Request):
    dispatcher: Dispatcher = request.app.dispatcher
    try:
        result = await dispatcher.dispatch(request)
    except DestroyedOnLoadError:
        return Response("Process destroyed on load", status_code=status.HTTP_502_BAD_GATEWAY)
    except LambdaTimeoutError:
        return Response("Lambda timeout", status_code=status.HTTP_408_REQUEST_TIMEOUT)

    if not result:
        return Response("No response", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
