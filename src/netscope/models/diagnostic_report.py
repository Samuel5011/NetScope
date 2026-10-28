from dataclasses import dataclass, field
from datetime import datetime

from netscope.models.dns_result import DNSResult
from netscope.models.ping_result import PingResult
from netscope.models.port_result import PortResult
from netscope.models.target import Target
from netscope.models.trace_result import TraceResult


@dataclass
class DiagnosticReport:
    target: Target
    generated_at: datetime
    dns: DNSResult | None = None
    ping: PingResult | None = None
    trace: TraceResult | None = None
    ports: list[PortResult] = field(default_factory=list)
