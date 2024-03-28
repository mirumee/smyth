from dataclasses import asdict

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from smyth.dispatcher.dispatcher import Dispatcher


async def status_endpoint(request: Request):
    dispatcher: Dispatcher = request.app.dispatcher

    response_data = {
        "lambda handlers": {},
        "config": asdict(dispatcher.config),
    }

    for process_group_name, process_group in dispatcher.process_groups.items():
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
