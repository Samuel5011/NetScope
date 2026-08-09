import argparse
import ipaddress

from netscope.diagnostics.dns import resolve_dns
from netscope.diagnostics.ping import ping_target
from netscope.diagnostics.port_scanner import scan_port
from netscope.exceptions import InvalidTargetError
from netscope.models.target import Target
from netscope.utils.validation import validate_target


def _get_target_type(value: str) -> str:
    try:
        ip = ipaddress.ip_address(value)

        if ip.version == 4:
            return "ipv4"

        return "ipv6"

    except ValueError:
        return "hostname"


def _create_target(value: str) -> Target:
    cleaned_value = validate_target(value)

    return Target(
        value=cleaned_value,
        target_type=_get_target_type(cleaned_value),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="netscope",
        description="Network diagnostic toolkit",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    dns_parser = subparsers.add_parser(
        "dns",
        help="Resolve a target using DNS",
    )
    dns_parser.add_argument("target")

    ping_parser = subparsers.add_parser(
        "ping",
        help="Ping a network target",
    )
    ping_parser.add_argument("target")

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan TCP ports on a target",
    )
    scan_parser.add_argument("target")
    scan_parser.add_argument(
        "--ports",
        default="22,80,443",
        help="Comma-separated TCP ports (default: 22,80,443)",
    )

    args = parser.parse_args()

    try:
        target = _create_target(args.target)

        if args.command == "dns":
            dns_result = resolve_dns(target)

            if dns_result.success:
                print(f"Target: {dns_result.target.value}")
                print(f"IP address: {dns_result.ip_address}")
                print(f"Response time: {dns_result.response_time_ms:.2f} ms")
            else:
                print(f"DNS lookup failed: {dns_result.error}")

        elif args.command == "ping":
            ping_result = ping_target(target)

            print(f"Target: {ping_result.target.value}")
            print(f"Reachable: {'Yes' if ping_result.reachable else 'No'}")

            if ping_result.response_time_ms is not None:
                print(f"Average latency: " f"{ping_result.response_time_ms:.2f} ms")

            if ping_result.packet_loss_percent is not None:
                print(f"Packet loss: " f"{ping_result.packet_loss_percent:.1f}%")

            if ping_result.error:
                print(f"Error: {ping_result.error}")

        elif args.command == "scan":
            try:
                ports = [int(port.strip()) for port in args.ports.split(",")]
            except ValueError:
                parser.error("Ports must be comma-separated numbers")

            for port in ports:
                if not 1 <= port <= 65535:
                    parser.error(f"Invalid port: {port}")

                port_result = scan_port(target, port)

                status = "OPEN" if port_result.open else "CLOSED"

                service = (
                    f" ({port_result.service})"
                    if port_result.service is not None
                    else ""
                )

                print(f"{port}/tcp: {status}{service}")

    except InvalidTargetError as exc:
        parser.error(str(exc))
