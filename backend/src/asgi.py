import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from fastapi.staticfiles import StaticFiles

from src.app.helpers.register_modules import register_modules
from src.app.middleware import add_middlewares
from src.logger import setup_logger
from src.settings import settings

logger = setup_logger()


app = FastAPI(
    title=settings.display_name,
    version=settings.app_version,
)
add_middlewares(app)

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    if token != settings.api_key.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid token")
    return token


dependencies = [Depends(verify_token)]


# Register core modules
register_modules(
    app,
    path="src/app/modules/core",
    prefix="/core",
    dependencies=dependencies,
    exclude_dependencies=["info"],
)

# Register custom modules
register_modules(
    app,
    path="src/app/modules/custom",
    prefix="/custom",
    dependencies=dependencies,
)

# Register auto-generated modules
register_modules(
    app,
    path="src/app/modules/auto",
    prefix="/auto",
    dependencies=dependencies,
    tags=["auto"],
)
