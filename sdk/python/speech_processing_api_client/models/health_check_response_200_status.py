from enum import Enum

class HealthCheckResponse200Status(str, Enum):
    DEGRADED = "degraded"
    HEALTHY = "healthy"
    UNAVAILABLE = "unavailable"

    def __str__(self) -> str:
        return str(self.value)
