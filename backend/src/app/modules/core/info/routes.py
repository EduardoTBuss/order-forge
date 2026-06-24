import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.modules.core.info.logic.health import get_server_health
from src.app.modules.core.info.logic.swagger import convert_openapi3_to_swagger
from src.app.modules.core.info.logic.test_runner import (
    get_test_status,
    get_valid_modules,
    trigger_test_run,
)
from src.app.modules.core.info.schemas.io import (
    ServerHealthOutput,
    TestModulesOutput,
    TestRunStatusOutput,
    TestRunTriggerOutput,
)
from src.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["info"])

security = HTTPBearer()


def _verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verifies the API key for protected endpoints."""
    if credentials.credentials != settings.api_key.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


@router.get("/health", response_model=ServerHealthOutput)
def health_check() -> ServerHealthOutput:
    """
    Returns the current health status of the server including uptime, CPU, memory, and disk usage.
    """
    try:
        return get_server_health()
    except Exception:
        logger.exception("Health check failed.")
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.get("/swagger")
def swagger_spec_get(
    request: Request,
    tags: list[str] = Query(
        default=[
            "blob_storage",
            "cosmosdb",
            "postgresql",
        ],
        description="Only include endpoints whose operation/router tags intersect this list.",
    ),
) -> JSONResponse:
    """Return the Swagger 2.0 JSON converted from the FastAPI OpenAPI 3 spec, filtered by tags."""
    openapi_v3 = request.app.openapi()
    swagger_v2 = convert_openapi3_to_swagger(
        openapi_v3, allowed_tags=tags, request=request
    )
    return JSONResponse(content=swagger_v2)


@router.get("/tests/modules", response_model=TestModulesOutput)
def list_test_modules(_: str = Depends(_verify_token)) -> TestModulesOutput:
    """Returns the list of available module names for test filtering."""
    return TestModulesOutput(modules=get_valid_modules())


@router.post("/tests/run", response_model=TestRunTriggerOutput)
def run_tests(
    _: str = Depends(_verify_token),
    module: str | None = Query(
        default=None,
        description="Filter tests to a specific module (e.g., 'postgresql', 'cosmosdb', 'blob_storage'). "
        "If not provided, runs all tests. Use GET /tests/modules to list available modules.",
        examples=["postgresql", "cosmosdb", "blob_storage"],
    ),
) -> TestRunTriggerOutput:
    """
    Triggers a test run in the background. Requires API key authentication.

    Optionally filter tests to a specific module using the `module` query parameter.
    """
    try:
        # Validate module name if provided
        if module and module not in get_valid_modules():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid module '{module}'. Use GET /tests/modules to list available modules.",
            )

        triggered = trigger_test_run(module=module)

        if triggered:
            msg = (
                f"Test run started for module '{module}'."
                if module
                else "Test run started for all modules."
            )
            return TestRunTriggerOutput(
                triggered=True,
                message=f"{msg} Check /core/info/tests/status for progress.",
                module=module,
            )
        else:
            return TestRunTriggerOutput(
                triggered=False,
                message="Tests are already running. Wait for completion.",
                module=None,
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to trigger test run.")
        raise HTTPException(status_code=500, detail="Failed to trigger test run.")


@router.get("/tests/status", response_model=TestRunStatusOutput)
def tests_status(_: str = Depends(_verify_token)) -> TestRunStatusOutput:
    """Returns the status of the current or last test run. Requires API key authentication."""
    try:
        status = get_test_status()
        return TestRunStatusOutput(
            is_running=status.is_running,
            started_at=status.started_at,
            finished_at=status.finished_at,
            exit_code=status.exit_code,
            report_path=status.report_path,
            module=status.module,
        )
    except Exception:
        logger.exception("Failed to get test status.")
        raise HTTPException(status_code=500, detail="Failed to get test status.")
