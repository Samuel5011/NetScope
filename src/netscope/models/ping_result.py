from dataclasses import dataclass

from netscope.models.target import Target


@dataclass
class PingResult:
    target: Target
    reachable: bool
    response_time_ms: float | None
    packet_loss_percent: float | None
    error: str | None = None
