import socket

from netscope.models.port_result import PortResult
from netscope.models.target import Target
from netscope.utils.validation import validate_port


def scan_port(
    target: Target,
    port: int,
    timeout: float = 1.0,
) -> PortResult:
    """Try one TCP port and report whether it accepted a connection."""
    validate_port(port)
    if timeout <= 0:
        raise ValueError("Timeout must be greater than 0")

    try:
        # A successful TCP connection is enough to treat the port as open.
        with socket.create_connection(
            (target.value, port),
            timeout=timeout,
        ):
            try:
                # Some ports do not have a known service name on the OS.
                service = socket.getservbyport(port, "tcp")
            except OSError:
                service = None

            return PortResult(
                target=target,
                port=port,
                open=True,
                service=service,
                error=None,
            )

    except (ConnectionRefusedError, TimeoutError, OSError) as exc:
        return PortResult(
            target=target,
            port=port,
            open=False,
            service=None,
            error=str(exc),
        )


def scan_ports(
    target: Target,
    ports: list[int],
    timeout: float = 1.0,
) -> list[PortResult]:
    """Scan several TCP ports in the supplied order."""
    return [scan_port(target, port, timeout) for port in ports]
