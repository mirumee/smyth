class DispatcherError(Exception):
    pass


class ProcessDefinitionNotFoundError(DispatcherError):
    pass


class NoAvailableProcessError(DispatcherError):
    pass


class DestroyedOnLoadError(DispatcherError):
    pass


class LambdaTimeoutError(DispatcherError):
    pass
