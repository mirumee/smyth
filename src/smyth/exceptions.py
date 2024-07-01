class LambdaRuntimeError(Exception):
    """Generic Lambda Runtime exception."""


class ConfigFileNotFoundError(LambdaRuntimeError):
    """Config file not found."""


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


class LambdaInvocationError(DispatcherError):
    pass
