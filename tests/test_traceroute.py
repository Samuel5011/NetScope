import platform
import subprocess

from netscope.diagnostics.traceroute import parse_traceroute_output, trace_route
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
