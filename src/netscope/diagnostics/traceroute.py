import ipaddress
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


def _is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value.rstrip("%"))
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
    identity = _LATENCY_PATTERN.sub("", value).replace("*", " ")
    if address is not None:
        identity = identity.replace(f"({address})", "")
        identity = identity.replace(f"[{address}]", "")
        identity = identity.replace(address, "")

    identity = " ".join(identity.split())
    if not identity or identity.lower().startswith("request timed out"):
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
        hops.append(
            TraceHop(
                number=number,
                address=address,
                hostname=_find_hostname(hop_details, address),
                response_times_ms=[
                    float(value) for value in _LATENCY_PATTERN.findall(hop_details)
                ],
            )
        )

    return hops


def _build_command(
    target: Target,
    max_hops: int,
    timeout: float,
) -> list[str]:
    if get_platform_name() == "windows":
        return [
            "tracert",
            "-d",
            "-h",
            str(max_hops),
            "-w",
            str(round(timeout * 1000)),
            target.value,
        ]

    return [
        "traceroute",
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
    if timeout <= 0:
        raise ValueError("Timeout must be greater than 0")

    try:
        command = _build_command(target, max_hops, timeout)
    except UnsupportedPlatformError as exc:
        return TraceResult(target=target, hops=[], success=False, error=str(exc))

    result = run_command(command, max_hops * timeout * 3 + 5)
    if result.error is not None:
        return TraceResult(target=target, hops=[], success=False, error=result.error)

    hops = parse_traceroute_output(result.stdout)
    error = result.stderr.strip() or None
    if result.returncode != 0 and error is None:
        error = "Traceroute failed"

    return TraceResult(
        target=target,
        hops=hops,
        success=result.returncode == 0,
        error=error,
    )
