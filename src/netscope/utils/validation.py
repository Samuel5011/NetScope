import ipaddress
from collections.abc import Iterable

from netscope.exceptions import InvalidPortError, InvalidTargetError


def validate_port(port: int) -> int:
    if not 1 <= port <= 65535:
        raise InvalidPortError(f"Port must be between 1 and 65535: {port}")
    return port


def parse_ports(value: str) -> list[int]:
    """Parse comma-separated ports and inclusive ranges."""
    if not value.strip():
        raise InvalidPortError("At least one port is required")

    ports: list[int] = []
    seen: set[int] = set()

    for item in value.split(","):
        item = item.strip()
        if not item:
            raise InvalidPortError("Port list contains an empty value")

        item_ports: Iterable[int]
        if "-" in item:
            bounds = item.split("-")
            if len(bounds) != 2 or not all(bound.strip().isdigit() for bound in bounds):
                raise InvalidPortError(f"Invalid port range: {item}")

            start = validate_port(int(bounds[0]))
            end = validate_port(int(bounds[1]))
            if start > end:
                raise InvalidPortError(f"Port range must be ascending: {item}")
            item_ports = range(start, end + 1)
        else:
            if not item.isdigit():
                raise InvalidPortError(f"Invalid port: {item}")
            item_ports = [validate_port(int(item))]

        for port in item_ports:
            if port not in seen:
                ports.append(port)
                seen.add(port)

    return ports


def _is_hostname_valid(hostname: str) -> bool:
    labels = hostname.split(".")

    for label in labels:
        if label == "":
            return False

        if label.startswith("-") or label.endswith("-"):
            return False

        for character in label:
            if not (character.isalnum() or character == "-"):
                return False

    return True


def validate_target(value: str) -> str:
    cleaned_target = value.strip()

    if cleaned_target == "":
        raise InvalidTargetError("Target cannot be empty")

    if "://" in cleaned_target:
        raise InvalidTargetError("Target must be a hostname or IP address, not a URL")

    if "/" in cleaned_target:
        raise InvalidTargetError("Target must not contain a path")

    try:
        ipaddress.ip_address(cleaned_target)
        return cleaned_target
    except ValueError:
        pass

    if _is_hostname_valid(cleaned_target):
        return cleaned_target

    raise InvalidTargetError("Target must be a valid hostname or IP address")
