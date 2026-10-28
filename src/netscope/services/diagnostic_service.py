from netscope.diagnostics.dns import resolve_dns
from netscope.diagnostics.ping import ping_target
from netscope.diagnostics.port_scanner import scan_ports
from netscope.diagnostics.traceroute import trace_route
from netscope.models.diagnostic_report import DiagnosticReport
from netscope.models.target import Target
from netscope.services.report_service import create_report


def run_diagnostics(
    target: Target,
    ports: list[int],
    *,
    port_timeout: float = 1.0,
    max_hops: int = 30,
    trace_timeout: float = 2.0,
) -> DiagnosticReport:
    """Run the standard diagnostics and combine their results."""
    dns_result = resolve_dns(target)
    ping_result = ping_target(target)
    trace_result = trace_route(target, max_hops=max_hops, timeout=trace_timeout)
    port_results = scan_ports(target, ports, timeout=port_timeout)

    return create_report(
        target,
        dns=dns_result,
        ping=ping_result,
        trace=trace_result,
        ports=port_results,
    )
