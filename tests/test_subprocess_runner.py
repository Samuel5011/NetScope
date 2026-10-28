import subprocess

from netscope.utils.subprocess_runner import run_command


def test_run_command_success(monkeypatch) -> None:
    completed = subprocess.CompletedProcess(
        args=["example"], returncode=0, stdout="output", stderr=""
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    result = run_command(["example"], timeout=1)

    assert result.returncode == 0
    assert result.stdout == "output"
    assert result.error is None


def test_run_command_handles_timeout(monkeypatch) -> None:
    def time_out(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["example"], timeout=2)

    monkeypatch.setattr(subprocess, "run", time_out)

    result = run_command(["example"], timeout=2)

    assert result.returncode is None
    assert result.error == "Command timed out after 2 seconds"


def test_run_command_handles_missing_executable(monkeypatch) -> None:
    def not_found(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", not_found)

    result = run_command(["example"], timeout=1)

    assert result.returncode is None
    assert result.error == "Required command not found: example"
