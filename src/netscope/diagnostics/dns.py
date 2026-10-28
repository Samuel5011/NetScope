import socket
import time

from netscope.models.dns_result import DNSResult
from netscope.models.target import Target


def resolve_dns(target: Target) -> DNSResult:
    """Resolve a target and keep lookup failures in the result."""
    start = time.perf_counter()

    try:
        addresses = socket.getaddrinfo(
            target.value,
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
        if not addresses:
            raise socket.gaierror("No addresses found")

        ip_address = str(addresses[0][4][0])
        response_time_ms = (time.perf_counter() - start) * 1000

        return DNSResult(
            target=target,
            ip_address=ip_address,
            success=True,
            response_time_ms=response_time_ms,
        )

    except socket.gaierror as exc:
        # Bad hostnames are still a normal diagnostic result, not a crash.
        response_time_ms = (time.perf_counter() - start) * 1000

        return DNSResult(
            target=target,
            ip_address=None,
            success=False,
            response_time_ms=response_time_ms,
            error=str(exc),
        )
