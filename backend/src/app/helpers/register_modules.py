import importlib
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI

logger = logging.getLogger(__name__)

load_dotenv()


def _register_module(
    app: FastAPI,
    module_name: str,
    module_path: str,
    prefix: str,
    dependencies: list,
    path: str,
    tags: list | None = None,
):
    if not os.path.isdir(module_path):
        logger.warning(f"Module path does not exist: {module_path}")
        return False
    try:
        # Import the module dynamically
        module = importlib.import_module(
            f"{path.replace('/', '.')}.{module_name}.routes"
        )
        # Get the router from the module
        router = getattr(module, "router")
        # Define route
        route = f"{prefix}/{module_name}".replace("_", "-")
        # Include the router in the FastAPI app
        app.include_router(
            router,
            prefix=route,
            tags=tags,
            dependencies=dependencies,
            generate_unique_id_function=lambda route: f"{module_name}.{route.name}",
        )
        logger.info(
            f"Successfully registered router for module {module_name}. Router prefix: {route}"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to register router for module {module_name}: {e}")
        return False


def register_modules(
    app: FastAPI,
    path: str,
    prefix: str,
    dependencies: list,
    tags: list | None = None,
    exclude_dependencies: list[str] = [],
) -> None:
    """
    Register modules within the custom directory in the FastAPI app.
    """
    modules = [
        name
        for name in os.listdir(path)
        if not name.startswith("__") and os.path.isdir(os.path.join(path, name))
    ]
    modules = sorted(modules)

    for module in modules:
        # Register the latest module version with the base name as the prefix
        module_path = os.path.join(path, module)
        _register_module(
            app=app,
            module_name=module,
            module_path=module_path,
            prefix=prefix,
            dependencies=dependencies if module not in exclude_dependencies else [],
            path=path,
            tags=tags,
        )
