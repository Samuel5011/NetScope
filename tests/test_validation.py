import pytest

from netscope.exceptions import InvalidTargetError
from netscope.utils.validation import validate_target


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