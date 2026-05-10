import importlib
import pkgutil

import app.modules


def discover_cog_extensions() -> list[str]:
    extensions: list[str] = []
    for module_info in pkgutil.iter_modules(app.modules.__path__):
        extension = f"app.modules.{module_info.name}.cog"
        try:
            importlib.import_module(extension)
        except ModuleNotFoundError:
            continue
        extensions.append(extension)
    return extensions
