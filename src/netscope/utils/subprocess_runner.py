import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int | None
    error: str | None = None
    timed_out: bool = False


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def run_command(command: list[str], timeout: float) -> CommandResult:
    """Run an external command and normalize execution failures."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            stdout=_as_text(exc.stdout),
            stderr=_as_text(exc.stderr),
            returncode=None,
            error=f"Command timed out after {timeout:g} seconds",
            timed_out=True,
        )
    except FileNotFoundError:
        return CommandResult(
            stdout="",
            stderr="",
            returncode=None,
            error=f"Required command not found: {command[0]}",
        )
    except PermissionError:
        return CommandResult(
            stdout="",
            stderr="",
            returncode=None,
            error=f"Permission denied while running: {command[0]}",
        )
    except OSError as exc:
        return CommandResult(
            stdout="",
            stderr="",
            returncode=None,
            error=f"Could not run {command[0]}: {exc}",
        )

    return CommandResult(
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode,
    )
