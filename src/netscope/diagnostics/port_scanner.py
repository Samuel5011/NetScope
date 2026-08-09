import socket

from netscope.models.port_result import PortResult
from netscope.models.target import Target


def scan_port(
    target: Target,
    port: int,
    timeout: float = 1.0,
) -> PortResult:
    """Try one TCP port and report whether it accepted a connection."""
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
