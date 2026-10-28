import json
from datetime import UTC, datetime

from netscope.models.dns_result import DNSResult
from netscope.models.ping_result import PingResult
from netscope.models.port_result import PortResult
from netscope.models.target import Target
from netscope.models.trace_result import TraceHop, TraceResult
from netscope.services.report_service import (
    create_report,
    format_json_report,
    format_text_report,
    report_to_dict,
)


def test_create_report_uses_supplied_results() -> None:
    target = Target(value="example.com", target_type="hostname")
    dns = DNSResult(target, "93.184.216.34", True, 2.5)
    generated_at = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)

    report = create_report(target, dns=dns, generated_at=generated_at)

    assert report.target == target
    assert report.generated_at == generated_at
    assert report.dns == dns
    assert report.ping is None
    assert report.trace is None
    assert report.ports == []


def test_format_text_report_includes_all_sections() -> None:
    target = Target(value="example.com", target_type="hostname")
    generated_at = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
    report = create_report(
        target,
        generated_at=generated_at,
        dns=DNSResult(target, "93.184.216.34", True, 2.5),
        ping=PingResult(target, True, 10.25, 0.0),
        trace=TraceResult(
            target,
            [TraceHop(1, "192.168.1.1", "router.local", [1.0, 1.2])],
            True,
        ),
        ports=[PortResult(target, 443, True, "open", "https")],
    )

    output = format_text_report(report)

    assert "NetScope diagnostic report" in output
    assert "Target: example.com (hostname)" in output
    assert "Generated: 2026-10-28T12:00:00+00:00" in output
    assert "DNS\n  Status: success" in output
    assert "Ping\n  Reachable: yes" in output
    assert "Traceroute\n   1  router.local (192.168.1.1)" in output
    assert "TCP ports\n  443/tcp: OPEN (https)" in output


def test_format_text_report_includes_errors_and_missing_values() -> None:
    target = Target(value="missing.example", target_type="hostname")
    report = create_report(
        target,
        generated_at=datetime(2026, 10, 28, tzinfo=UTC),
        dns=DNSResult(target, None, False, 1.0, "Name not known"),
        ping=PingResult(target, False, None, None, "Required command not found"),
        trace=TraceResult(target, [], False, "Traceroute failed"),
        ports=[
            PortResult(
                target,
                443,
                False,
                "filtered",
                error="Connection timed out",
            )
        ],
    )

    output = format_text_report(report)

    assert "Address: unavailable" in output
    assert "Average latency: unavailable" in output
    assert "Packet loss: unavailable" in output
    assert "No hops returned" in output
    assert "443/tcp: FILTERED - Connection timed out" in output


def test_report_to_dict_has_stable_json_structure() -> None:
    target = Target(value="example.com", target_type="hostname")
    report = create_report(
        target,
        generated_at=datetime(2026, 10, 28, 12, 0, tzinfo=UTC),
        dns=DNSResult(target, "93.184.216.34", True, 2.5),
        ports=[PortResult(target, 443, True, "open", "https")],
    )

    data = report_to_dict(report)

    assert data["target"] == {"value": "example.com", "type": "hostname"}
    assert data["generated_at"] == "2026-10-28T12:00:00+00:00"
    assert data["dns"] == {
        "success": True,
        "ip_address": "93.184.216.34",
        "response_time_ms": 2.5,
        "error": None,
    }
    assert data["ping"] is None
    assert data["traceroute"] is None
    assert data["ports"] == [
        {
            "port": 443,
            "state": "open",
            "open": True,
            "service": "https",
            "error": None,
        }
    ]


def test_format_json_report_returns_valid_json() -> None:
    target = Target(value="example.com", target_type="hostname")
    report = create_report(
        target,
        generated_at=datetime(2026, 10, 28, 12, 0, tzinfo=UTC),
        ping=PingResult(target, True, 4.2, 0.0),
    )

    output = format_json_report(report)

    assert json.loads(output)["ping"]["reachable"] is True
