import pytest

from netscope.exceptions import InvalidPortError, InvalidTargetError
from netscope.utils.validation import parse_ports, validate_target


def test_valid_hostname() -> None:
    assert validate_target("google.com") == "google.com"


def test_strips_whitespace() -> None:
    assert validate_target("  google.com  ") == "google.com"


def test_whitespace_only_target_rejected() -> None:
    with pytest.raises(InvalidTargetError):
        validate_target("      ")


def test_valid_ipv4() -> None:
    assert validate_target("8.8.8.8") == "8.8.8.8"


def test_valid_ipv6() -> None:
    assert validate_target("2001:4860:4860::8888") == "2001:4860:4860::8888"


def test_empty_target_rejected() -> None:
    with pytest.raises(InvalidTargetError):
        validate_target("")


def test_url_rejected() -> None:
    with pytest.raises(InvalidTargetError):
        validate_target("https://google.com")


def test_path_rejected() -> None:
    with pytest.raises(InvalidTargetError):
        validate_target("google.com/path")


def test_invalid_hostname_rejected() -> None:
    with pytest.raises(InvalidTargetError):
        validate_target("-google.com")


def test_parse_ports_accepts_lists_and_ranges() -> None:
    assert parse_ports("22, 80, 8000-8002") == [22, 80, 8000, 8001, 8002]


def test_parse_ports_removes_duplicates() -> None:
    assert parse_ports("80,80,79-81") == [80, 79, 81]


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("", "At least one port is required"),
        ("80,", "Port list contains an empty value"),
        ("http", "Invalid port: http"),
        ("80-", "Invalid port range: 80-"),
        ("100-90", "Port range must be ascending: 100-90"),
        ("0", "Port must be between 1 and 65535: 0"),
        ("65536", "Port must be between 1 and 65535: 65536"),
    ],
)
def test_parse_ports_rejects_invalid_values(value: str, message: str) -> None:
    with pytest.raises(InvalidPortError, match=message):
        parse_ports(value)
