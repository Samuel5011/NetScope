import argparse
import ipaddress

from netscope.diagnostics.dns import resolve_dns
from netscope.diagnostics.ping import ping_target
from netscope.diagnostics.port_scanner import scan_ports
from netscope.diagnostics.traceroute import trace_route
from netscope.exceptions import InvalidPortError, InvalidTargetError
from netscope.models.target import Target
from netscope.services.report_service import create_report, format_json_report
from netscope.utils.validation import parse_ports, validate_target


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


def _add_json_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the diagnostic result as JSON",
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
    _add_json_argument(dns_parser)

    ping_parser = subparsers.add_parser(
        "ping",
        help="Ping a network target",
    )
    ping_parser.add_argument("target")
    _add_json_argument(ping_parser)

    trace_parser = subparsers.add_parser(
        "trace",
        help="Trace the network path to a target",
    )
    trace_parser.add_argument("target")
    trace_parser.add_argument(
        "--max-hops",
        type=int,
        default=30,
        help="Maximum number of hops (default: 30)",
    )
    trace_parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Seconds to wait for each response (default: 2.0)",
    )
    _add_json_argument(trace_parser)

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan TCP ports on a target",
    )
    scan_parser.add_argument("target")
    scan_parser.add_argument(
        "--ports",
        default="22,80,443",
        help="TCP ports and ranges, such as 22,80,8000-8010 (default: 22,80,443)",
    )
    scan_parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Connection timeout in seconds (default: 1.0)",
    )
    _add_json_argument(scan_parser)

    args = parser.parse_args()

    try:
        target = _create_target(args.target)

        if args.command == "dns":
            dns_result = resolve_dns(target)

            if args.json:
                print(format_json_report(create_report(target, dns=dns_result)))
            elif dns_result.success:
                print(f"Target: {dns_result.target.value}")
                print(f"IP address: {dns_result.ip_address}")
                print(f"Response time: {dns_result.response_time_ms:.2f} ms")
            else:
                print(f"DNS lookup failed: {dns_result.error}")

        elif args.command == "ping":
            ping_result = ping_target(target)

            if args.json:
                print(format_json_report(create_report(target, ping=ping_result)))
            else:
                print(f"Target: {ping_result.target.value}")
                print(f"Reachable: {'Yes' if ping_result.reachable else 'No'}")

                if ping_result.response_time_ms is not None:
                    print(f"Average latency: " f"{ping_result.response_time_ms:.2f} ms")

                if ping_result.packet_loss_percent is not None:
                    print(f"Packet loss: " f"{ping_result.packet_loss_percent:.1f}%")

                if ping_result.error:
                    print(f"Error: {ping_result.error}")

        elif args.command == "trace":
            if args.max_hops < 1:
                parser.error("Maximum hops must be at least 1")
            if args.timeout <= 0:
                parser.error("Timeout must be greater than 0")

            trace_result = trace_route(
                target,
                max_hops=args.max_hops,
                timeout=args.timeout,
            )

            if args.json:
                print(format_json_report(create_report(target, trace=trace_result)))
            else:
                print(f"Traceroute to {trace_result.target.value}")
                for hop in trace_result.hops:
                    identity = hop.address or "*"
                    if hop.hostname is not None:
                        identity = f"{hop.hostname} ({identity})"
                    latencies = " ".join(
                        f"{response_time:.2f} ms"
                        for response_time in hop.response_times_ms
                    )
                    print(f"{hop.number:2}  {identity}  {latencies}".rstrip())

                if trace_result.error:
                    print(f"Error: {trace_result.error}")

        elif args.command == "scan":
            if args.timeout <= 0:
                parser.error("Timeout must be greater than 0")
            ports = parse_ports(args.ports)
            port_results = scan_ports(target, ports, timeout=args.timeout)

            if args.json:
                print(format_json_report(create_report(target, ports=port_results)))
            else:
                for port_result in port_results:
                    status = port_result.state.upper()

                    service = (
                        f" ({port_result.service})"
                        if port_result.service is not None
                        else ""
                    )
                    error = (
                        f" - {port_result.error}"
                        if port_result.error is not None
                        else ""
                    )

                    print(f"{port_result.port}/tcp: {status}{service}{error}")

    except (InvalidPortError, InvalidTargetError) as exc:
        parser.error(str(exc))
