from dataclasses import dataclass

from netscope.models.target import Target


@dataclass
class PortResult:
    target: Target
    port: int
    open: bool
    service: str | None = None
    error: str | None = None
