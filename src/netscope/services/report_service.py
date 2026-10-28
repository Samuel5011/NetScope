from datetime import UTC, datetime

from netscope.models.diagnostic_report import DiagnosticReport
from netscope.models.dns_result import DNSResult
from netscope.models.ping_result import PingResult
from netscope.models.port_result import PortResult
from netscope.models.target import Target
from netscope.models.trace_result import TraceHop, TraceResult


def create_report(
    target: Target,
    *,
    dns: DNSResult | None = None,
    ping: PingResult | None = None,
    trace: TraceResult | None = None,
    ports: list[PortResult] | None = None,
    generated_at: datetime | None = None,
) -> DiagnosticReport:
    """Create a report from any available diagnostic results."""
    return DiagnosticReport(
        target=target,
        generated_at=generated_at or datetime.now(UTC),
        dns=dns,
        ping=ping,
        trace=trace,
        ports=list(ports or []),
    )


def _format_optional_measurement(
    label: str,
    value: float | None,
    suffix: str,
    precision: int,
) -> str:
    if value is None:
        return f"{label}: unavailable"
    return f"{label}: {value:.{precision}f}{suffix}"


def _format_trace_hop(hop: TraceHop) -> str:
    identity = hop.address or "*"
    if hop.hostname is not None:
        identity = f"{hop.hostname} ({identity})"
    timings = " ".join(f"{timing:.2f} ms" for timing in hop.response_times_ms)
    return f"  {hop.number:2}  {identity}  {timings}".rstrip()


def format_text_report(report: DiagnosticReport) -> str:
    """Format a diagnostic report for terminal output."""
    lines = [
        "NetScope diagnostic report",
        f"Target: {report.target.value} ({report.target.target_type})",
        f"Generated: {report.generated_at.isoformat()}",
    ]

    if report.dns is not None:
        lines.extend(
            [
                "",
                "DNS",
                f"  Status: {'success' if report.dns.success else 'failed'}",
                f"  Address: {report.dns.ip_address or 'unavailable'}",
                f"  Response time: {report.dns.response_time_ms:.2f} ms",
            ]
        )
        if report.dns.error is not None:
            lines.append(f"  Error: {report.dns.error}")

    if report.ping is not None:
        lines.extend(
            [
                "",
                "Ping",
                f"  Reachable: {'yes' if report.ping.reachable else 'no'}",
                "  "
                + _format_optional_measurement(
                    "Average latency",
                    report.ping.response_time_ms,
                    " ms",
                    2,
                ),
                "  "
                + _format_optional_measurement(
                    "Packet loss",
                    report.ping.packet_loss_percent,
                    "%",
                    1,
                ),
            ]
        )
        if report.ping.error is not None:
            lines.append(f"  Error: {report.ping.error}")

    if report.trace is not None:
        lines.extend(["", "Traceroute"])
        if report.trace.hops:
            lines.extend(_format_trace_hop(hop) for hop in report.trace.hops)
        else:
            lines.append("  No hops returned")
        if report.trace.error is not None:
            lines.append(f"  Error: {report.trace.error}")

    if report.ports:
        lines.extend(["", "TCP ports"])
        for port in report.ports:
            service = f" ({port.service})" if port.service is not None else ""
            error = f" - {port.error}" if port.error is not None else ""
            lines.append(f"  {port.port}/tcp: {port.state.upper()}{service}{error}")

    return "\n".join(lines)
