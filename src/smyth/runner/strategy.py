from smyth.types import RunnerProcessProtocol, SmythHandlerState


def round_robin(
    handler_name: str, processes: dict[str, list[RunnerProcessProtocol]]
) -> RunnerProcessProtocol:
    """This strategy, not typical for AWS Lambda's behavior, is beneficial
    during development. It rotates among Lambda Processes for each request,
    given that concurrency is set higher than `1`. This approach encourages
    developers to avoid relying on global state across requests, promoting
    best practices in serverless application design."""
    return sorted(
        processes[handler_name],
        key=lambda process: process.last_used_timestamp,
    )[0]


def first_warm(
    handler_name: str, processes: dict[str, list[RunnerProcessProtocol]]
) -> RunnerProcessProtocol:
    """This strategy prioritizes the use of the first available Lambda Process
    in a "warm" state to handle incoming requests. If no warm instances are
    available, it initiates a "cold start". This behavior more closely mimics
    the operational dynamics of AWS Lambda, where reusing warm instances can
    lead to faster response times."""
    best_candidate = None
    for process in processes[handler_name]:
        if process.state == SmythHandlerState.WARM:
            return process
        if process.state == SmythHandlerState.COLD and not best_candidate:
            best_candidate = process

    if best_candidate is None:
        raise Exception("No process available")

    return best_candidate
