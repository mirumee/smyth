from importlib import import_module


def import_attribute(python_path: str):
    module_name, handler_name = python_path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, handler_name)
