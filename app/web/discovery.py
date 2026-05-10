import importlib
import pkgutil

from fastapi import APIRouter

import app.modules


def discover_module_routers() -> list[APIRouter]:
    routers: list[APIRouter] = []
    for module_info in pkgutil.iter_modules(app.modules.__path__):
        module_name = f"app.modules.{module_info.name}.routes"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            routers.append(router)
    return routers
