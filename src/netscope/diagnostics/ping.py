import re

from netscope.exceptions import UnsupportedPlatformError
from netscope.models.ping_result import PingResult
from netscope.models.target import Target
from netscope.utils.platform import get_platform_name
from netscope.utils.subprocess_runner import run_command

_UNIX_PACKET_LOSS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)%\s*packet loss")
_WINDOWS_PACKET_LOSS_PATTERN = re.compile(r"\((\d+(?:\.\d+)?)%\s*loss\)", re.IGNORECASE)
_UNIX_LATENCY_PATTERN = re.compile(
    r"(?:round-trip|rtt).*?=\s*[\d.]+/([\d.]+)/",
)
_WINDOWS_LATENCY_PATTERN = re.compile(r"Average\s*=\s*(\d+)ms", re.IGNORECASE)


def _parse_first_float(
    patterns: tuple[re.Pattern[str], ...], output: str
) -> float | None:
    for pattern in patterns:
        match = pattern.search(output)
        if match:
            return float(match.group(1))
    return None


def ping_target(target: Target, count: int = 4, timeout: float = 10.0) -> PingResult:
    """Run ping and return the useful parts as a result object."""
    if count < 1:
        raise ValueError("Ping count must be at least 1")
    if timeout <= 0:
        raise ValueError("Timeout must be greater than 0")

    try:
        system = get_platform_name()
    except UnsupportedPlatformError as exc:
        return PingResult(target, False, None, None, str(exc))

    count_flag = "-n" if system == "windows" else "-c"
    command = ["ping", count_flag, str(count), target.value]
    result = run_command(command, timeout)

    if result.error is not None:
        return PingResult(target, False, None, None, result.error)

    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    packet_loss = _parse_first_float(
        (_UNIX_PACKET_LOSS_PATTERN, _WINDOWS_PACKET_LOSS_PATTERN),
        output,
    )
    response_time = _parse_first_float(
        (_UNIX_LATENCY_PATTERN, _WINDOWS_LATENCY_PATTERN),
        output,
    )
    reachable = result.returncode == 0
    error = None if reachable else result.stderr.strip() or "Target unreachable"

    return PingResult(
        target=target,
        reachable=reachable,
        response_time_ms=response_time,
        packet_loss_percent=packet_loss,
        error=error,
    )
