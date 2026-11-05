import ipaddress
import math
import re

from netscope.exceptions import UnsupportedPlatformError
from netscope.models.target import Target
from netscope.models.trace_result import TraceHop, TraceResult
from netscope.utils.platform import get_platform_name
from netscope.utils.subprocess_runner import run_command

_HOP_PATTERN = re.compile(r"^\s*(\d+)\s+(.*)$")
_LATENCY_PATTERN = re.compile(r"<?(\d+(?:\.\d+)?)\s*ms", re.IGNORECASE)
_PARENTHESIZED_ADDRESS_PATTERN = re.compile(r"\(([^()]+)\)")
_BRACKETED_ADDRESS_PATTERN = re.compile(r"\[([^\[\]]+)\]")
_MAX_COMMAND_TIMEOUT = 60.0


def _is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value.split("%", maxsplit=1)[0])
    except ValueError:
        return False
    return True


def _find_address(value: str) -> str | None:
    for pattern in (_PARENTHESIZED_ADDRESS_PATTERN, _BRACKETED_ADDRESS_PATTERN):
        match = pattern.search(value)
        if match and _is_ip_address(match.group(1)):
            return match.group(1)

    for token in reversed(value.split()):
        candidate = token.strip("()[]")
        if _is_ip_address(candidate):
            return candidate

    return None


def _find_hostname(value: str, address: str | None) -> str | None:
    if address is None:
        return None

    identity = _LATENCY_PATTERN.sub("", value).replace("*", " ")
    if address is not None:
        identity = identity.replace(f"({address})", "")
        identity = identity.replace(f"[{address}]", "")
        identity = identity.replace(address, "")

    identity = " ".join(identity.split())
    if not identity or identity.startswith("!"):
        return None
    if identity.lower().startswith(("request timed out", "destination host")):
        return None
    return identity.split(maxsplit=1)[0]


def parse_traceroute_output(output: str) -> list[TraceHop]:
    """Parse hop lines emitted by traceroute or tracert."""
    hops: list[TraceHop] = []

    for line in output.splitlines():
        match = _HOP_PATTERN.match(line)
        if match is None:
            continue

        number = int(match.group(1))
        hop_details = match.group(2)
        address = _find_address(hop_details)
        response_times = [
            float(value) for value in _LATENCY_PATTERN.findall(hop_details)
        ]
        unreachable = "*" in hop_details or any(
            marker in hop_details.lower() for marker in ("timed out", "unreachable")
        )
        if address is None and not response_times and not unreachable:
            continue

        hops.append(
            TraceHop(
                number=number,
                address=address,
                hostname=_find_hostname(hop_details, address),
                response_times_ms=response_times,
            )
        )

    return hops


def _build_command(
    target: Target,
    max_hops: int,
    timeout: float,
) -> list[str]:
    system = get_platform_name()
    if system == "windows":
        return [
            "tracert",
            "-d",
            "-h",
            str(max_hops),
            "-w",
            str(round(timeout * 1000)),
            target.value,
        ]

    if system == "darwin" and target.target_type == "ipv6":
        executable = "traceroute6"
        family_flag: list[str] = []
    else:
        executable = "traceroute"
        family_flag = ["-6"] if target.target_type == "ipv6" else []

    return [
        executable,
        *family_flag,
        "-n",
        "-m",
        str(max_hops),
        "-w",
        str(timeout),
        target.value,
    ]


def trace_route(
    target: Target,
    max_hops: int = 30,
    timeout: float = 2.0,
) -> TraceResult:
    """Trace the network path to a target."""
    if max_hops < 1:
        raise ValueError("Maximum hops must be at least 1")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Timeout must be greater than 0")

    try:
        command = _build_command(target, max_hops, timeout)
    except UnsupportedPlatformError as exc:
        return TraceResult(target=target, hops=[], success=False, error=str(exc))

    command_timeout = min(max_hops * timeout * 3 + 5, _MAX_COMMAND_TIMEOUT)
    result = run_command(command, command_timeout)
    hops = parse_traceroute_output(result.stdout)
    if result.error is not None:
        return TraceResult(target=target, hops=hops, success=False, error=result.error)

    success = result.returncode == 0 and bool(hops)
    error: str | None = None
    if result.returncode != 0:
        error = result.stderr.strip() or "Traceroute failed"
    elif not hops:
        error = "Traceroute produced no hop data"

    return TraceResult(
        target=target,
        hops=hops,
        success=success,
        error=error,
    )
