class LambdaRuntimeError(Exception):
    """Generic Lambda Runtime exception."""


class ConfigFileNotFoundError(LambdaRuntimeError):
    """Config file not found."""
