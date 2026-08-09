from dataclasses import dataclass

from netscope.models.target import Target


@dataclass
class DNSResult:
    target: Target
    ip_address: str | None
    success: bool
    response_time_ms: float
    error: str | None = None
