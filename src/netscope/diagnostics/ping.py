import platform
import re
import subprocess

from netscope.models.ping_result import PingResult
from netscope.models.target import Target


def ping_target(target: Target) -> PingResult:
    """Run ping and return the useful parts as a result object."""
    system = platform.system().lower()

    # Windows and Unix-like ping commands use different flags for the count.
    if system == "windows":
        command = ["ping", "-n", "4", target.value]
    else:
        command = ["ping", "-c", "4", target.value]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        output = result.stdout

        # Pull the percentage before "% packet loss" from ping output.
        packet_loss_match = re.search(
            r"(\d+(?:\.\d+)?)% packet loss",
            output,
        )

        packet_loss = float(packet_loss_match.group(1)) if packet_loss_match else None

        # The middle value in min/avg/max is the average response time.
        response_time_match = re.search(
            r"(?:round-trip|rtt).*?=\s*[\d.]+/([\d.]+)/",
            output,
        )

        response_time = (
            float(response_time_match.group(1)) if response_time_match else None
        )

        return PingResult(
            target=target,
            reachable=result.returncode == 0,
            response_time_ms=response_time,
            packet_loss_percent=packet_loss,
            error=None if result.returncode == 0 else "Target unreachable",
        )

    except (subprocess.TimeoutExpired, OSError) as exc:
        return PingResult(
            target=target,
            reachable=False,
            response_time_ms=None,
            packet_loss_percent=None,
            error=str(exc),
        )
