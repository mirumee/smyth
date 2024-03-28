from starlette.requests import Request


async def generate_context_data(request: Request, timeout: float | None = None):
    """
    The data returned by this function is passed to the 
    `smyth.runner.FaneContext` as kwargs.
    """
    context = {}
    if timeout is not None:
        context["timeout"] = timeout
    return context
