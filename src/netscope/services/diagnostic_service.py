from netscope.diagnostics.dns import resolve_dns
from netscope.diagnostics.ping import ping_target
from netscope.diagnostics.port_scanner import scan_ports
from netscope.diagnostics.traceroute import trace_route
from netscope.models.diagnostic_report import DiagnosticReport
from netscope.models.dns_result import DNSResult
from netscope.models.ping_result import PingResult
from netscope.models.port_result import PortResult
from netscope.models.target import Target
from netscope.models.trace_result import TraceResult
from netscope.services.report_service import create_report


def _unexpected_error(name: str, exc: Exception) -> str:
    detail = str(exc) or exc.__class__.__name__
    return f"Unexpected {name} error: {detail}"


def run_diagnostics(
    target: Target,
    ports: list[int],
    *,
    port_timeout: float = 1.0,
    max_hops: int = 30,
    trace_timeout: float = 2.0,
) -> DiagnosticReport:
    """Run the standard diagnostics and combine their results."""
    try:
        dns_result = resolve_dns(target)
    except Exception as exc:  # noqa: BLE001 - isolate combined diagnostics
        dns_result = DNSResult(
            target=target,
            ip_address=None,
            success=False,
            response_time_ms=0.0,
            error=_unexpected_error("DNS", exc),
        )

    try:
        ping_result = ping_target(target)
    except Exception as exc:  # noqa: BLE001 - isolate combined diagnostics
        ping_result = PingResult(
            target=target,
            reachable=False,
            response_time_ms=None,
            packet_loss_percent=None,
            error=_unexpected_error("ping", exc),
        )

    try:
        trace_result = trace_route(
            target,
            max_hops=max_hops,
            timeout=trace_timeout,
        )
    except Exception as exc:  # noqa: BLE001 - isolate combined diagnostics
        trace_result = TraceResult(
            target=target,
            hops=[],
            success=False,
            error=_unexpected_error("traceroute", exc),
        )

    try:
        port_results = scan_ports(target, ports, timeout=port_timeout)
    except Exception as exc:  # noqa: BLE001 - isolate combined diagnostics
        error = _unexpected_error("port scan", exc)
        port_results = [
            PortResult(
                target=target,
                port=port,
                open=False,
                state="error",
                error=error,
            )
            for port in ports
        ]

    return create_report(
        target,
        dns=dns_result,
        ping=ping_result,
        trace=trace_result,
        ports=port_results,
    )
