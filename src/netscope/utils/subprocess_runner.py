import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int | None
    error: str | None = None


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
    except subprocess.TimeoutExpired:
        return CommandResult(
            stdout="",
            stderr="",
            returncode=None,
            error=f"Command timed out after {timeout:g} seconds",
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
