import ipaddress
from netscope.exceptions import InvalidTargetError

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