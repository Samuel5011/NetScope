import platform
import subprocess

from netscope.diagnostics.traceroute import (
    _build_command,
    parse_traceroute_output,
    trace_route,
)
from netscope.models.target import Target


def test_parse_unix_traceroute_output() -> None:
    output = """traceroute to example.com (93.184.216.34), 30 hops max
 1  router.local (192.168.1.1)  1.123 ms  0.456 ms  0.789 ms
 2  * * *
 3  93.184.216.34  10.100 ms  11.200 ms  12.300 ms
 4  fe80::1%en0  2.000 ms  2.100 ms  2.200 ms
"""

    hops = parse_traceroute_output(output)

    assert len(hops) == 4
    assert hops[0].number == 1
    assert hops[0].hostname == "router.local"
    assert hops[0].address == "192.168.1.1"
    assert hops[0].response_times_ms == [1.123, 0.456, 0.789]
    assert hops[1].address is None
    assert hops[1].response_times_ms == []
    assert hops[2].address == "93.184.216.34"
    assert hops[3].address == "fe80::1%en0"


def test_parse_windows_tracert_output() -> None:
    output = """Tracing route to example.com [93.184.216.34]
  1    <1 ms    <1 ms     1 ms  router.local [192.168.1.1]
  2     *        *        *     Request timed out.
"""

    hops = parse_traceroute_output(output)

    assert len(hops) == 2
    assert hops[0].hostname == "router.local"
    assert hops[0].address == "192.168.1.1"
    assert hops[0].response_times_ms == [1.0, 1.0, 1.0]
    assert hops[1].address is None


def test_trace_route_success(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")
    completed = subprocess.CompletedProcess(
        args=["traceroute"],
        returncode=0,
        stdout=" 1  192.168.1.1  1.000 ms  2.000 ms  3.000 ms\n",
        stderr="",
    )

    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    result = trace_route(target, max_hops=10, timeout=1.5)

    assert result.success is True
    assert result.error is None
    assert len(result.hops) == 1
    assert result.hops[0].address == "192.168.1.1"


def test_trace_route_handles_missing_command(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")

    def missing_command(*args, **kwargs):
        raise FileNotFoundError("traceroute was not found")

    monkeypatch.setattr(subprocess, "run", missing_command)

    result = trace_route(target)

    assert result.success is False
    assert result.hops == []
    assert result.error == "Required command not found: traceroute"


def test_parse_traceroute_skips_malformed_lines_and_keeps_unreachable_hops() -> None:
    output = """ 1  malformed hop data
 2  * * *
 3  Destination host unreachable.
 4  203.0.113.5  5.000 ms !H
"""

    hops = parse_traceroute_output(output)

    assert [hop.number for hop in hops] == [2, 3, 4]
    assert hops[0].address is None
    assert hops[1].address is None
    assert hops[2].address == "203.0.113.5"
    assert hops[2].hostname is None


def test_trace_route_rejects_output_without_hops(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")
    completed = subprocess.CompletedProcess(
        args=["traceroute"],
        returncode=0,
        stdout="traceroute to example.com, 30 hops max\nmalformed output\n",
        stderr="",
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    result = trace_route(target)

    assert result.success is False
    assert result.hops == []
    assert result.error == "Traceroute produced no hop data"


def test_trace_route_timeout_keeps_partial_hops_and_caps_duration(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")
    timeouts: list[float] = []

    def time_out(command, **kwargs):
        timeouts.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired(
            command,
            timeout=kwargs["timeout"],
            output=" 1  192.168.1.1  1.000 ms\n",
        )

    monkeypatch.setattr(subprocess, "run", time_out)

    result = trace_route(target, max_hops=30, timeout=2)

    assert timeouts == [60.0]
    assert result.success is False
    assert [hop.address for hop in result.hops] == ["192.168.1.1"]
    assert result.error == "Command timed out after 60 seconds"


def test_traceroute_uses_platform_ipv6_commands(monkeypatch) -> None:
    target = Target(value="2001:db8::1", target_type="ipv6")

    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    assert _build_command(target, 10, 1.0)[0] == "traceroute6"

    monkeypatch.setattr(platform, "system", lambda: "Linux")
    assert _build_command(target, 10, 1.0)[:2] == ["traceroute", "-6"]

    monkeypatch.setattr(platform, "system", lambda: "Windows")
    assert _build_command(target, 10, 1.0)[0] == "tracert"


def test_macos_traceroute_uses_integer_wait_time(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    command = _build_command(target, 10, 1.5)

    assert command[command.index("-w") + 1] == "2"
