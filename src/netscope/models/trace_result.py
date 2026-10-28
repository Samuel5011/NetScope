from dataclasses import dataclass, field

from netscope.models.target import Target


@dataclass
class TraceHop:
    number: int
    address: str | None
    hostname: str | None
    response_times_ms: list[float] = field(default_factory=list)


@dataclass
class TraceResult:
    target: Target
    hops: list[TraceHop]
    success: bool
    error: str | None = None
