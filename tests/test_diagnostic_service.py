from netscope.models.dns_result import DNSResult
from netscope.models.ping_result import PingResult
from netscope.models.port_result import PortResult
from netscope.models.target import Target
from netscope.models.trace_result import TraceHop, TraceResult
from netscope.services import diagnostic_service


def test_run_diagnostics_combines_all_results(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")
    dns = DNSResult(target, "93.184.216.34", True, 1.5)
    ping = PingResult(target, True, 4.2, 0.0)
    trace = TraceResult(
        target,
        [TraceHop(1, "192.168.1.1", None, [1.0])],
        True,
    )
    port_results = [PortResult(target, 443, True, "open", "https")]
    trace_arguments: list[tuple[int, float]] = []
    scan_arguments: list[tuple[list[int], float]] = []

    monkeypatch.setattr(diagnostic_service, "resolve_dns", lambda value: dns)
    monkeypatch.setattr(diagnostic_service, "ping_target", lambda value: ping)

    def fake_trace(value, max_hops, timeout):
        trace_arguments.append((max_hops, timeout))
        return trace

    def fake_scan(value, ports, timeout):
        scan_arguments.append((ports, timeout))
        return port_results

    monkeypatch.setattr(diagnostic_service, "trace_route", fake_trace)
    monkeypatch.setattr(diagnostic_service, "scan_ports", fake_scan)

    report = diagnostic_service.run_diagnostics(
        target,
        [80, 443],
        port_timeout=0.25,
        max_hops=12,
        trace_timeout=1.5,
    )

    assert report.target == target
    assert report.dns == dns
    assert report.ping == ping
    assert report.trace == trace
    assert report.ports == port_results
    assert trace_arguments == [(12, 1.5)]
    assert scan_arguments == [([80, 443], 0.25)]
