import time
from datetime import datetime, timezone

import psutil

from src.app.modules.core.info.schemas.io import ServerHealthOutput
from src.app.modules.core.info.schemas.server_status import ServerStatus

start_time: float = time.time()


def get_server_health() -> ServerHealthOutput:
    """
    Collects and returns the current health status of the server.
    """

    uptime = time.time() - start_time
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    load = psutil.getloadavg()
    timestamp = datetime.now(timezone.utc).isoformat()

    status = ServerStatus.OK

    if any(value > 98 for value in [cpu, mem, disk]):
        status = ServerStatus.CRITICAL
    elif any(value > 90 for value in [cpu, mem, disk]):
        status = ServerStatus.DEGRADED

    return ServerHealthOutput(
        status=status,
        uptime=round(uptime, 2),
        cpu_usage=cpu,
        memory_usage=mem,
        disk_usage=disk,
        load_average=load,
        timestamp=timestamp,
    )
