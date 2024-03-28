from importlib import import_module
import logging


class SmythStatusRouteFilter(logging.Filter):

    def __init__(self, name: str = "", smyth_path_prefix: str = "") -> None:
        super().__init__(name)
        self.smyth_path_prefix = smyth_path_prefix

    def filter(self, record):
        return record.getMessage().find(self.smyth_path_prefix) == -1


def import_attribute(python_path: str):
    module_name, handler_name = python_path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, handler_name)
