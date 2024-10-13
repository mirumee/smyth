class SmythRuntimeError(Exception):
    """Generic Lambda Runtime exception."""


class ConfigFileNotFoundError(SmythRuntimeError):
    """Config file not found."""


class DispatcherError(SmythRuntimeError):
    pass


class ProcessDefinitionNotFoundError(DispatcherError):
    pass


class NoAvailableProcessError(DispatcherError):
    pass


class DestroyedOnLoadError(DispatcherError):
    pass


class SubprocessError(SmythRuntimeError):
    """Generic subprocess exception."""


class LambdaHandlerLoadError(SubprocessError):
    """Error loading a Lambda handler."""


class LambdaTimeoutError(SubprocessError):
    """Lambda timeout."""


class LambdaInvocationError(SubprocessError):
    """Error invoking a Lambda."""
