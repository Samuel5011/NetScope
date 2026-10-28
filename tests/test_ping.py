import platform
import subprocess

from netscope.diagnostics.ping import ping_target
from netscope.models.target import Target


def test_ping_success(monkeypatch) -> None:
    target = Target(
        value="google.com",
        target_type="hostname",
    )

    fake_result = subprocess.CompletedProcess(
        args=["ping"],
        returncode=0,
        stdout=(
            "4 packets transmitted, 4 packets received, 0.0% packet loss\n"
            "round-trip min/avg/max/stddev = 4.100/5.200/6.300/0.500 ms\n"
        ),
        stderr="",
    )

    def fake_run(*args, **kwargs):
        return fake_result

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = ping_target(target)

    assert result.reachable is True
    assert result.packet_loss_percent == 0.0
    assert result.response_time_ms == 5.2
    assert result.error is None
    assert result.target == target


def test_ping_failure(monkeypatch) -> None:
    target = Target(
        value="invalid.example",
        target_type="hostname",
    )

    fake_result = subprocess.CompletedProcess(
        args=["ping"],
        returncode=1,
        stdout="100.0% packet loss\n",
        stderr="",
    )

    def fake_run(*args, **kwargs):
        return fake_result

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = ping_target(target)

    assert result.reachable is False
    assert result.packet_loss_percent == 100.0
    assert result.response_time_ms is None
    assert result.error is not None


def test_ping_parses_windows_output(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")
    fake_result = subprocess.CompletedProcess(
        args=["ping"],
        returncode=0,
        stdout=(
            "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n"
            "Minimum = 4ms, Maximum = 6ms, Average = 5ms\n"
        ),
        stderr="",
    )
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return fake_result

    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = ping_target(target)

    assert commands == [["ping", "-n", "4", "example.com"]]
    assert result.reachable is True
    assert result.packet_loss_percent == 0.0
    assert result.response_time_ms == 5.0


def test_ping_reports_unsupported_platform(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")
    monkeypatch.setattr(platform, "system", lambda: "Plan 9")

    result = ping_target(target)

    assert result.reachable is False
    assert result.error == "Unsupported platform: Plan 9"
