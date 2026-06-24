import logging
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Valid module names that can be used for filtering
VALID_MODULES = [
    "postgresql",
    "cosmosdb",
    "blob_storage",
    "info",
]


def _get_report_path(module: str | None = None) -> str:
    """Returns the report path based on module filter."""
    if module:
        return f"/static/test-report-{module}.html"
    return "/static/test-report.html"


@dataclass
class TestRunStatus:
    is_running: bool = False
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    report_path: str = "/static/test-report.html"
    module: str | None = None


_test_status = TestRunStatus()
_lock = threading.Lock()


def get_test_status() -> TestRunStatus:
    """Returns the current test run status."""
    with _lock:
        return TestRunStatus(
            is_running=_test_status.is_running,
            started_at=_test_status.started_at,
            finished_at=_test_status.finished_at,
            exit_code=_test_status.exit_code,
            report_path=_test_status.report_path,
            module=_test_status.module,
        )


def get_valid_modules() -> list[str]:
    """Returns the list of valid module names for filtering."""
    return VALID_MODULES.copy()


def _run_pytest(module: str | None = None) -> None:
    """Runs pytest in a subprocess and updates the status."""
    global _test_status

    try:
        backend_root = Path(__file__).parents[6]

        # Build pytest command with module-specific report path
        report_filename = f"test-report-{module}.html" if module else "test-report.html"
        cmd = [
            "pytest",
            f"--html=static/{report_filename}",
            "--self-contained-html",
            "-q",
        ]

        # Add module path if specified
        if module:
            # Check both core and custom module paths
            core_path = (
                backend_root / "src" / "app" / "modules" / "core" / module / "tests.py"
            )
            custom_path = (
                backend_root
                / "src"
                / "app"
                / "modules"
                / "custom"
                / module
                / "tests.py"
            )

            if core_path.exists():
                cmd.append(str(core_path.relative_to(backend_root)))
            elif custom_path.exists():
                cmd.append(str(custom_path.relative_to(backend_root)))
            else:
                logger.warning("No tests.py found for module: %s", module)
                # Still run but pytest will report no tests found
                cmd.append(f"src/app/modules/*/{module}/tests.py")

        logger.info(
            "Starting test run from: %s with command: %s", backend_root, " ".join(cmd)
        )

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=backend_root,
        )

        with _lock:
            _test_status.exit_code = result.returncode
            _test_status.finished_at = datetime.now(timezone.utc)
            _test_status.is_running = False

        if result.returncode == 0:
            logger.info("Test run completed successfully")
        else:
            logger.warning(
                "Test run completed with failures. Exit code: %d", result.returncode
            )
            logger.debug("Test stdout: %s", result.stdout)
            logger.debug("Test stderr: %s", result.stderr)

    except Exception:
        logger.exception("Test run failed with exception")
        with _lock:
            _test_status.exit_code = -1
            _test_status.finished_at = datetime.now(timezone.utc)
            _test_status.is_running = False


def trigger_test_run(module: str | None = None) -> bool:
    """
    Triggers a test run in the background. Returns False if tests are already running.

    Args:
        module: Optional module name to filter tests. If None, runs all tests.
    """
    global _test_status

    with _lock:
        if _test_status.is_running:
            return False

        _test_status.is_running = True
        _test_status.started_at = datetime.now(timezone.utc)
        _test_status.finished_at = None
        _test_status.exit_code = None
        _test_status.module = module
        _test_status.report_path = _get_report_path(module)

    thread = threading.Thread(target=_run_pytest, args=(module,), daemon=True)
    thread.start()

    return True
