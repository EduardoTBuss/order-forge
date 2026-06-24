from datetime import datetime

from pydantic import BaseModel, Field


class ServerHealthOutput(BaseModel):
    status: str = Field(..., examples=["ok"], description="Overall server status")
    uptime: float = Field(
        ..., examples=[123.45], description="Server uptime in seconds"
    )
    cpu_usage: float = Field(..., examples=[12.5], description="CPU usage percentage")
    memory_usage: float = Field(
        ..., examples=[45.3], description="Memory usage percentage"
    )
    disk_usage: float = Field(..., examples=[66.7], description="Disk usage percentage")
    load_average: tuple[float, float, float] = Field(
        ...,
        examples=[(0.1, 0.2, 0.3)],
        description="System load average over 1, 5, 15 minutes",
    )
    timestamp: str = Field(
        ..., examples=["2025-08-01T12:34:56Z"], description="Current UTC timestamp"
    )


class TestRunTriggerOutput(BaseModel):
    triggered: bool = Field(..., description="Whether a new test run was triggered")
    message: str = Field(..., description="Status message")
    module: str | None = Field(
        None,
        description="Module filter applied to this test run",
        examples=["postgresql", "cosmosdb"],
    )


class TestModulesOutput(BaseModel):
    modules: list[str] = Field(
        ...,
        description="List of available module names for test filtering",
        examples=[["postgresql", "cosmosdb", "blob_storage"]],
    )


class TestRunStatusOutput(BaseModel):
    is_running: bool = Field(..., description="Whether tests are currently running")
    started_at: datetime | None = Field(None, description="When the test run started")
    finished_at: datetime | None = Field(None, description="When the test run finished")
    exit_code: int | None = Field(
        None, description="Exit code (0=success, non-zero=failures)"
    )
    report_path: str = Field(..., description="Path to the HTML test report")
    module: str | None = Field(
        None,
        description="Module filter used for this test run (None = all tests)",
        examples=["postgresql", "cosmosdb", "blob_storage"],
    )
