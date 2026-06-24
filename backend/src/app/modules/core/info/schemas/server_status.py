from enum import StrEnum


class ServerStatus(StrEnum):
    """
    Represents the overall health status of the server.
    """

    OK = "ok"
    DEGRADED = "degraded"
    CRITICAL = "critical"
