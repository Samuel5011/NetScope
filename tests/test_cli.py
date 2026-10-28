import json
import sys
from datetime import UTC, datetime

import pytest

from netscope import cli
from netscope.models.dns_result import DNSResult
from netscope.models.ping_result import PingResult
from netscope.models.port_result import PortResult
from netscope.models.target import Target
from netscope.models.trace_result import TraceHop, TraceResult
from netscope.services.report_service import create_report


def _set_arguments(monkeypatch, *arguments: str) -> None:
    monkeypatch.setattr(sys, "argv", ["netscope", *arguments])


def test_dns_command_text_output(monkeypatch, capsys) -> None:
    _set_arguments(monkeypatch, "dns", "example.com")

    def fake_resolve(target: Target) -> DNSResult:
        return DNSResult(target, "93.184.216.34", True, 1.25)

    monkeypatch.setattr(cli, "resolve_dns", fake_resolve)

    cli.main()

    assert capsys.readouterr().out == (
        "Target: example.com\n" "IP address: 93.184.216.34\n" "Response time: 1.25 ms\n"
    )


def test_dns_command_json_output(monkeypatch, capsys) -> None:
    _set_arguments(monkeypatch, "dns", "example.com", "--json")

    def fake_resolve(target: Target) -> DNSResult:
        return DNSResult(target, "93.184.216.34", True, 1.25)

    monkeypatch.setattr(cli, "resolve_dns", fake_resolve)

    cli.main()
    output = json.loads(capsys.readouterr().out)

    assert output["target"] == {"value": "example.com", "type": "hostname"}
    assert output["dns"]["ip_address"] == "93.184.216.34"
    assert output["ping"] is None


def test_ping_command_text_output(monkeypatch, capsys) -> None:
    _set_arguments(monkeypatch, "ping", "example.com")

    def fake_ping(target: Target) -> PingResult:
        return PingResult(target, True, 5.25, 0.0)

    monkeypatch.setattr(cli, "ping_target", fake_ping)

    cli.main()

    assert capsys.readouterr().out == (
        "Target: example.com\n"
        "Reachable: Yes\n"
        "Average latency: 5.25 ms\n"
        "Packet loss: 0.0%\n"
    )


def test_trace_command_passes_options_and_formats_hops(monkeypatch, capsys) -> None:
    _set_arguments(
        monkeypatch,
        "trace",
        "example.com",
        "--max-hops",
        "12",
        "--timeout",
        "1.5",
    )
    received: list[tuple[int, float]] = []

    def fake_trace(target: Target, max_hops: int, timeout: float) -> TraceResult:
        received.append((max_hops, timeout))
        return TraceResult(
            target,
            [TraceHop(1, "192.168.1.1", "router.local", [1.0])],
            True,
        )

    monkeypatch.setattr(cli, "trace_route", fake_trace)

    cli.main()

    assert received == [(12, 1.5)]
    assert capsys.readouterr().out == (
        "Traceroute to example.com\n 1  router.local (192.168.1.1)  1.00 ms\n"
    )


def test_scan_command_parses_ranges_and_formats_states(monkeypatch, capsys) -> None:
    _set_arguments(
        monkeypatch,
        "scan",
        "example.com",
        "--ports",
        "80,443-444",
        "--timeout",
        "0.25",
    )
    received: list[tuple[list[int], float]] = []

    def fake_scan(target: Target, ports: list[int], timeout: float) -> list[PortResult]:
        received.append((ports, timeout))
        return [
            PortResult(target, 80, True, "open", "http"),
            PortResult(target, 443, False, "closed"),
            PortResult(target, 444, False, "filtered", error="Connection timed out"),
        ]

    monkeypatch.setattr(cli, "scan_ports", fake_scan)

    cli.main()

    assert received == [([80, 443, 444], 0.25)]
    assert capsys.readouterr().out == (
        "80/tcp: OPEN (http)\n"
        "443/tcp: CLOSED\n"
        "444/tcp: FILTERED - Connection timed out\n"
    )


def test_diagnose_command_formats_combined_report(monkeypatch, capsys) -> None:
    _set_arguments(monkeypatch, "diagnose", "example.com", "--ports", "443")
    target = Target(value="example.com", target_type="hostname")
    report = create_report(
        target,
        generated_at=datetime(2026, 10, 28, 12, 0, tzinfo=UTC),
        dns=DNSResult(target, "93.184.216.34", True, 1.0),
        ping=PingResult(target, True, 5.0, 0.0),
        trace=TraceResult(target, [], True),
        ports=[PortResult(target, 443, True, "open", "https")],
    )

    monkeypatch.setattr(cli, "run_diagnostics", lambda *args, **kwargs: report)

    cli.main()
    output = capsys.readouterr().out

    assert "NetScope diagnostic report" in output
    assert "DNS\n  Status: success" in output
    assert "Ping\n  Reachable: yes" in output
    assert "Traceroute\n  No hops returned" in output
    assert "TCP ports\n  443/tcp: OPEN (https)" in output


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (("ping", "https://example.com"), "not a URL"),
        (("scan", "example.com", "--ports", "100-90"), "must be ascending"),
        (("trace", "example.com", "--max-hops", "0"), "at least 1"),
        (
            ("diagnose", "example.com", "--port-timeout", "0"),
            "Port timeout must be greater than 0",
        ),
    ],
)
def test_cli_rejects_invalid_arguments(monkeypatch, capsys, arguments, message) -> None:
    _set_arguments(monkeypatch, *arguments)

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    assert message in capsys.readouterr().err
